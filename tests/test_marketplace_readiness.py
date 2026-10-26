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
from inspect_agensi_zip import inspect


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

    def test_resource_secret_blocks_packaging(self):
        scripts = self.root / "first-skill" / "scripts"
        scripts.mkdir()
        (scripts / "helper.py").write_text(
            'TOKEN = "sk-or-v1-' + "a" * 48 + '"\n', encoding="utf-8")
        findings = scan(self.root)["findings"]
        self.assertTrue(any(x["code"] == "openrouter_key" and
                            x["path"] == "first-skill/scripts/helper.py" for x in findings))
        with self.assertRaisesRegex(ValueError, "openrouter_key"):
            create_pack(self.root, Path(self.temp.name) / "package.zip", ["first-skill"])

    def test_root_pdf_not_in_package(self):
        (self.root / "borrower.pdf").write_bytes(b"private sample")
        self.assertIn("non_catalog_root_file", [x["code"] for x in scan(self.root)["findings"]])
        target = Path(self.temp.name) / "package.zip"
        result = create_pack(self.root, target, ["first-skill"])
        self.assertEqual(result["skills"], ["first-skill"])
        with ZipFile(target) as zf:
            names = zf.namelist()
        self.assertIn("first-skill/SKILL.md", names)
        self.assertIn("first-skill/references/usage.md", names)
        self.assertIn("LICENSE", names)
        self.assertNotIn("borrower.pdf", names)

    def test_block_if_symlink_in_skill(self):
        (self.root / "first-skill" / "shadow.txt").symlink_to(
            self.root / "first-skill" / "SKILL.md")
        with self.assertRaisesRegex(ValueError, "Symlinks not allowed"):
            create_pack(self.root, Path(self.temp.name) / "package.zip", ["first-skill"])

    def test_single_skill_package_has_one_top_folder(self):
        target = Path(self.temp.name) / "package.zip"
        create_pack(self.root, target, ["first-skill"])
        with ZipFile(target) as zipf:
            self.assertIn("first-skill/SKILL.md", zipf.namelist())
            self.assertNotIn("skills/first-skill/SKILL.md", zipf.namelist())

    def test_block_if_binary_in_skill(self):
        (self.root / "first-skill" / "payload.exe").write_bytes(b"exe")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            create_pack(self.root, Path(self.temp.name) / "package.zip", ["first-skill"])

    def test_video_pipeline_uses_argument_list_without_shell(self):
        import ast
        source = (Path(__file__).resolve().parents[1] /
                  "media-pipeline" / "scripts" / "idol-video.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("shell=True", source)
        self.assertIn("subprocess.run(cmd, capture_output=True", source)

    def test_post_build_zip_inspection_is_clean(self):
        target = Path(self.temp.name) / "package.zip"
        create_pack(self.root, target, ["first-skill"])
        result = inspect(target)
        self.assertEqual(result["verdict"], "static_pass")
        self.assertEqual(result["skills"], ["first-skill/SKILL.md"])

    def test_zip_inspector_rejects_path_traversal(self):
        target = Path(self.temp.name) / "malformed.zip"
        with ZipFile(target, "w") as zf:
            zf.writestr("../outside.txt", "unsafe")
            zf.writestr("first-skill/SKILL.md",
                        (self.root / "first-skill" / "SKILL.md").read_text())
        self.assertEqual(inspect(target)["verdict"], "invalid")
        self.assertTrue(any("Unsafe ZIP entry path" in b for b in inspect(target)["blockers"]))

    def test_zip_inspector_rejects_unsupported_payload(self):
        target = Path(self.temp.name) / "malformed.zip"
        with ZipFile(target, "w") as zf:
            zf.writestr("first-skill/SKILL.md",
                        (self.root / "first-skill" / "SKILL.md").read_text())
            zf.writestr("first-skill/binary.exe", b"not permitted")
        self.assertTrue(any("Unsupported file type" in b for b in inspect(target)["blockers"]))

    def test_zip_inspector_catches_invalid_python(self):
        target = Path(self.temp.name) / "broken-script.zip"
        with ZipFile(target, "w") as zf:
            zf.writestr("first-skill/SKILL.md",
                        (self.root / "first-skill" / "SKILL.md").read_text())
            zf.writestr("first-skill/scripts/run.py", "def bad(:\\n")
        self.assertTrue(any("Python syntax error" in b for b in inspect(target)["blockers"]))

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
