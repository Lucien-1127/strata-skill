#!/usr/bin/env python3
"""Build an allowlist-only Agensi ZIP; never archive the repository itself."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from audit_skills import CREDENTIALS, scan

ALLOWED_SUFFIXES = {".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml",
                    ".toml", ".csv", ".ts", ".js", ".xml", ".ini", ".cfg", ".html"}
EXCLUDED = {".git", ".archive", ".venv", "venv", "__pycache__", "node_modules"}
MAX_SKILLS = 50
MAX_FILES = 1000
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024


def create_pack(root: Path, output: Path, selected: list[str]) -> dict:
    root = root.resolve()
    output = output.resolve()
    if not selected or len(selected) > MAX_SKILLS or len(set(selected)) != len(selected):
        raise ValueError("Supply between 1 and 50 distinct skill names")
    if not root.is_dir():
        raise ValueError(f"Missing repository directory: {root}")
    audit = scan(root)
    by_name = {x["name"]: x for x in audit["skills"] if x["name"]}
    files = {}
    for name in selected:
        if name not in by_name:
            raise ValueError(f"Unknown skill name: {name}")
        entry = by_name[name]
        prefix = entry["path"].removesuffix("/SKILL.md")
        problems = [f for f in audit["findings"] if f["level"] == "BLOCKER"
                    and (f["path"] == entry["path"] or f["path"].startswith(prefix + "/"))]
        if problems:
            raise ValueError(f"Skill {name} has blocking audit findings: {problems}")
        folder = root / prefix
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink() or any(p in EXCLUDED for p in path.relative_to(folder).parts):
                continue
            if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name != ".env.example":
                raise ValueError(f"Unsupported or binary file in skill: {path.relative_to(root)}")
            data = path.read_bytes()
            try:
                content = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"Non-UTF8 resource: {path.relative_to(root)}") from exc
            for code, pattern in CREDENTIALS:
                if pattern.search(content):
                    raise ValueError(f"Potential {code} in {path.relative_to(root)}")
            if path.suffix == ".py" and len(data) > 20 * 1024:
                raise ValueError(f"Script over 20KB; split before Agensi submission: {path}")
            archive_path = f"skills/{name}/{path.relative_to(folder).as_posix()}"
            if archive_path in files:
                raise ValueError(f"Archive path collision: {archive_path}")
            files[archive_path] = data

    notice = "Strata Skill — curated AI agent skills\n\n"
    notice += "Each SKILL.md describes its prerequisites, limits, and permitted workflow.\n"
    notice += "Included skills: " + ", ".join(selected) + "\n"
    files["README.md"] = notice.encode("utf-8")
    license_file = root / "LICENSE"
    if license_file.is_file():
        files["LICENSE"] = license_file.read_bytes()
    if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_ARCHIVE_BYTES:
        raise ValueError("Agensi website upload limits exceeded (1000 files / 50MB)")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_relative_to(root):
        raise ValueError("Output ZIP must be outside the repository to avoid accidental tracking")
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in sorted(files.items()):
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return {"zip": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "skills": sorted(selected), "files": len(files), "size_bytes": output.stat().st_size}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("skills", nargs="+", help="Skill names from YAML frontmatter")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--out", type=Path, required=True, help="Output path outside the repository")
    args = p.parse_args(argv)
    try:
        result = create_pack(args.root, args.out, args.skills)
    except (ValueError, OSError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
