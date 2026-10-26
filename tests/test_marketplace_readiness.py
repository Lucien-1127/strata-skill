"""Deterministic safety and packaging regression tests. Run with unittest."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_skills import scan
from build_agensi_pack import create_pack


class MarketplaceReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repository"
        self.root.mkdir()
        (self.root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        (self.root / "first-skill").mkdir()
        (self.root / "first-skill" / "SKILL.md").write_text(
            "---\nname: first-skill\ndescription: Does one safe operation.\nversion: 1.0.0\n---\n"
            "\n# First Skill\n\n## Verification\nCheck the result.\n", encoding="utf-8")
        (self.root / "first-skill" / "references").mkdir()
        (self.root / "first-skill" / "references" / "usage.md").write_text(
            "Use the instructions as written.\n", encoding="utf-8")

    def test_valid_skill_has_no_blockers(self):
        result = scan(self.root)
        self.assertEqual(result["skill_count"], 1)
        self.assertEqual(result["summary"]["blockers"], 0)

    def test_missing_frontmatter_blocks(self):
        (self.root / "first-skill" / "SKILL.md").write_text("# bad\n", encoding="utf-8")
        codes = [x["code"] for x in scan(self.root)["findings"]]
        self.assertIn("invalid_frontmatter", codes)
        self.assertIn("invalid_name", codes)

    def test_duplicate_names_block(self):
        folder = self.root / "second"
        folder.mkdir()
        (folder / "SKILL.md").write_text(
            "---\nname: first-skill\ndescription: Duplicate.\n---\n", encoding="utf-8")
        self.assertIn("duplicate_skill_name", [x["code"] for x in scan(self.root)["findings"]])

    def test_private_key_blocks(self):
        file = self.root / "first-skill" / "SKILL.md"
        file.write_text(file.read_text() + "\n-----BEGIN OPENSSH PRIVATE KEY-----\n" + "A" * 80 + "\n-----END OPENSSH PRIVATE KEY-----\n", encoding="utf-8")
        self.assertIn("private_key", [x["code"] for x in scan(self.root)["findings"]])

    def test_root_pdf_not_in_package(self):
        (self.root / "borrower.pdf").write_bytes(b"private sample")
        self.assertIn("non_catalog_root_file", [x["code"] for x in scan(self.root)["findings"]])
        target = Path(self.temp.name) / "package.zip"
        result = create_pack(self.root, target, ["first-skill"])
        self.assertEqual(result["skills"], ["first-skill"])
        with ZipFile(target) as zf:
            names = zf.namelist()
        self.assertIn("skills/first-skill/SKILL.md", names)
        self.assertIn("skills/first-skill/references/usage.md", names)
        self.assertIn("LICENSE", names)
        self.assertNotIn("borrower.pdf", names)

    def test_block_if_binary_in_skill(self):
        (self.root / "first-skill" / "payload.exe").write_bytes(b"exe")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            create_pack(self.root, Path(self.temp.name) / "package.zip", ["first-skill"])

    def test_deterministic_archive(self):
        one = Path(self.temp.name) / "one.zip"
        two = Path(self.temp.name) / "two.zip"
        a = create_pack(self.root, one, ["first-skill"])
        b = create_pack(self.root, two, ["first-skill"])
        self.assertEqual(a["sha256"], b["sha256"])

    def test_pack_cap(self):
        with self.assertRaisesRegex(ValueError, "50"):
            create_pack(self.root, Path(self.temp.name) / "package.zip", ["first-skill"] * 51)

    def test_missing_local_reference_warning(self):
        file = self.root / "first-skill" / "SKILL.md"
        file.write_text(file.read_text() + "\n[Missing](references/no-such-file.md)\n", encoding="utf-8")
        self.assertIn("broken_local_link", [x["code"] for x in scan(self.root)["findings"]])


if __name__ == "__main__":
    unittest.main()
