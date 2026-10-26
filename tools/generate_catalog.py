#!/usr/bin/env python3
"""Generate the public SKILL.md inventory from filesystem facts, not manual counts."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from audit_skills import EXCLUDED


def catalog(root: Path) -> str:
    entries = defaultdict(list)
    for skill in sorted(root.rglob("SKILL.md")):
        parts = skill.relative_to(root).parts
        if any(part in EXCLUDED for part in parts):
            continue
        group = parts[0] if len(parts) > 2 else "standalone"
        name = parts[-2]
        path = "/".join(parts)
        entries[group].append((name, path))
    count = sum(map(len, entries.values()))
    lines = ["# Strata Skill Catalog", "",
             "> Generated from repository SKILL.md paths. Structural inventory only; not a claim of runtime compatibility or marketplace approval.", "",
             f"**Active skills: {count}** (archived skills excluded).", "",
             "| Group | Skills |", "| --- | ---: |"]
    for group in sorted(entries):
        lines.append(f"| {group} | {len(entries[group])} |")
    for group in sorted(entries):
        lines.extend(["", f"## {group} ({len(entries[group])})", ""])
        for name, path in sorted(entries[group]):
            lines.append(f"- [{name}](../{path})")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--output", type=Path, default=Path("docs/SKILL_CATALOG.md"))
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    result = catalog(args.root)
    destination = args.output if args.output.is_absolute() else args.root / args.output
    if args.check:
        if not destination.is_file() or destination.read_text(encoding="utf-8") != result:
            print(f"STALE CATALOG: regenerate with python tools/generate_catalog.py --root {args.root}")
            return 1
        print("Skill catalog is synchronized.")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(result, encoding="utf-8")
    print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
