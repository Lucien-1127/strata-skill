#!/usr/bin/env python3
"""Independent, read-only inspection of a candidate Agensi skill ZIP.

This validates packaging, structure, text-only content, manifest safety, and
Python syntax. It is NOT the Agensi security service, does not execute scripts,
and cannot establish third-party provenance or real agent compatibility.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import stat
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from audit_skills import CREDENTIALS, RISK_PATTERNS

TEXT_EXTENSIONS = {".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml",
                   ".toml", ".csv", ".ts", ".js", ".xml", ".ini", ".cfg", ".html"}
MAX_ZIP = 50 * 1024 * 1024
MAX_ENTRIES = 1000
MAX_SKILLS = 50
MAX_SUPPORTING_FILES = 200
MAX_CHARACTERS = 6_000_000
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_SCRIPT_BYTES = 20 * 1024
HEADER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def inspect(path: Path) -> dict:
    blockers = []
    warnings = []
    names = set()
    skill_paths = []
    character_count = 0
    size_total = 0
    scanned = 0

    if not path.is_file():
        return {"verdict": "invalid", "blockers": ["ZIP does not exist"], "warnings": []}
    if path.stat().st_size > MAX_ZIP:
        blockers.append("Compressed ZIP exceeds 50MB")
    try:
        with ZipFile(path, "r") as zf:
            entries = zf.infolist()
            if len(entries) > MAX_ENTRIES:
                blockers.append("ZIP has more than 1000 entries")
            file_entries = [z for z in entries if not z.is_dir()]
            if len(file_entries) > MAX_ENTRIES:
                blockers.append("ZIP contains more than 1000 files")
            size_total = sum(z.file_size for z in file_entries)
            if size_total > MAX_UNCOMPRESSED_BYTES:
                blockers.append("ZIP uncompressed size exceeds 50MB")
            for item in file_entries:
                item_name = item.filename
                parts = item_name.split("/")
                if (
                    not item_name or item_name.startswith("/")
                    or any(p in {"", ".", ".."} for p in parts)
                    or "\\" in item_name or ":" in item_name or "\x00" in item_name
                ):
                    blockers.append("Unsafe ZIP entry path")
                    continue
                if item_name in names:
                    blockers.append(f"Duplicate ZIP entry: {item_name}")
                names.add(item_name)
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode):
                    blockers.append(f"Symlink entry is prohibited: {item_name}")
                if Path(item_name).suffix.lower() not in TEXT_EXTENSIONS and Path(item_name).name not in {".env.example", "LICENSE"}:
                    blockers.append(f"Unsupported file type: {item_name}")
                    continue
                if item_name.endswith("/SKILL.md") or item_name == "SKILL.md":
                    skill_paths.append(item_name)
                if (item_name.endswith(".py") or item_name.endswith(".sh")) and item.file_size > MAX_SCRIPT_BYTES:
                    blockers.append(f"Executable text script over 20KB: {item_name}")
                if item.file_size > MAX_UNCOMPRESSED_BYTES:
                    blockers.append(f"Oversized individual file: {item_name}")
                    continue
                if size_total > MAX_UNCOMPRESSED_BYTES:
                    # Fail closed instead of decompressing an oversized archive.
                    continue
                raw = zf.read(item)
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    blockers.append(f"Non-UTF8 file: {item_name}")
                    continue
                character_count += len(text)
                scanned += 1
                for code, pattern in CREDENTIALS:
                    if pattern.search(text):
                        blockers.append(f"Possible credential {code} in {item_name}")
                for code, pattern in RISK_PATTERNS:
                    if pattern.search(text):
                        warnings.append(f"Review suspicious pattern {code} in {item_name}")
                if item_name.endswith(".py"):
                    try:
                        ast.parse(text, filename=item_name)
                    except SyntaxError as exc:
                        blockers.append(f"Python syntax error in {item_name}: line {exc.lineno}")
                if item_name.endswith("/SKILL.md") or item_name == "SKILL.md":
                    header = HEADER.match(text)
                    if header is None:
                        blockers.append(f"Missing frontmatter: {item_name}")
                    else:
                        fields = {}
                        for line in header.group(1).splitlines():
                            m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
                            if m:
                                key, val = m.group(1), m.group(2).strip().strip('"\'')
                                if key in fields:
                                    blockers.append(f"Duplicate frontmatter field in {item_name}: {key}")
                                fields[key] = val
                        if not NAME.fullmatch(fields.get("name", "")):
                            blockers.append(f"Invalid or absent skill name: {item_name}")
                        if not fields.get("description"):
                            blockers.append(f"Missing skill description: {item_name}")
                        if fields.get("name", "") != (parts[-2] if len(parts) > 1 else fields.get("name", "")):
                            warnings.append(f"Skill name/folder mismatch: {item_name}")
            if len(skill_paths) == 0:
                blockers.append("No SKILL.md found")
            if len(skill_paths) > MAX_SKILLS:
                blockers.append("More than 50 skills in one pack")
            if len(file_entries) - len(skill_paths) > MAX_SUPPORTING_FILES:
                blockers.append("More than 200 supporting files (agent delivery limit)")
            if character_count > MAX_CHARACTERS:
                blockers.append("More than 6 million text characters (delivery limit)")
            bad = zf.testzip() if size_total <= MAX_UNCOMPRESSED_BYTES else None
            if bad is not None:
                blockers.append(f"Damaged ZIP content: {bad}")
    except (OSError, BadZipFile, EOFError, RuntimeError, ValueError) as exc:
        blockers.append(f"Cannot safely inspect ZIP: {type(exc).__name__}")

    return {
        "verdict": "invalid" if blockers else "static_pass",
        "skills": sorted(skill_paths),
        "files": len(names),
        "scanned_utf8_files": scanned,
        "characters": character_count,
        "uncompressed_bytes": size_total,
        "blockers": blockers,
        "warnings": warnings,
        "limitations": "Not a platform approval, malware certification or proof of actual agent execution.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip_path", type=Path)
    args = p.parse_args()
    report = inspect(args.zip_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    sys.exit(main())
