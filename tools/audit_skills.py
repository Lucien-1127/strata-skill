#!/usr/bin/env python3
"""Read-only audit for portable AI Agent SKILL.md libraries (Python stdlib only)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXCLUDED = {".archive", ".git", ".venv", "venv", "node_modules", "__pycache__"}
PRIVATE_ROOT_NAMES = {".curator_state", ".usage.json.lock"}
PRIVATE_SUFFIXES = {".pdf", ".p12", ".pfx", ".pem", ".key", ".db", ".sqlite", ".sqlite3"}
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CREDENTIALS = (
    ("private_key", re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----")),
    ("openrouter_key", re.compile(r"\bsk-or-v1-[a-fA-F0-9]{32,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{30,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github_token", re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9_]{30,}\b")),
)
RISK_PATTERNS = (
    ("download_pipe_shell", re.compile(r"\b(?:curl|wget)\b[^\n]{0,240}\|\s*(?:sudo\s+)?(?:bash|sh)\b")),
    ("root_delete", re.compile(r"\brm\s+-rf\s+/(?:\s|$)")),
    ("shell_true", re.compile(r"\bshell\s*=\s*True\b")),
    ("os_system", re.compile(r"\bos\.system\s*\(")),
    ("world_writable", re.compile(r"\bchmod\s+777\b")),
)
LOCAL_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)#?]+)(?:#[^)]*)?\)")
FIELD = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):(?:\s+|$)(.*)$")


def scan(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    findings = []
    skills = []
    names = {}
    def add(level: str, code: str, path: Path, detail: str) -> None:
        findings.append(dict(level=level, code=code, path=path.relative_to(root).as_posix(), detail=detail))

    for f in sorted(root.rglob("SKILL.md")):
        if any(p in EXCLUDED for p in f.relative_to(root).parts):
            continue
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")
        sections = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
        fields = {}
        if sections is None:
            add("BLOCKER", "invalid_frontmatter", f, "Missing YAML --- delimiters")
        else:
            for line in sections.group(1).splitlines():
                m = FIELD.match(line)
                if m:
                    key, value = m.groups()
                    if key in fields:
                        add("BLOCKER", "duplicate_frontmatter_key", f, key)
                    fields[key] = value.strip().strip("'\"")
        name, description = fields.get("name", ""), fields.get("description", "")
        if not name or not NAME.fullmatch(name):
            add("BLOCKER", "invalid_name", f, "Required lowercase-hyphenated name")
        if not description or description in {"|", ">"}:
            add("BLOCKER", "missing_description", f, "Description must be a nonempty single-line scalar")
        if name and name != f.parent.name:
            add("WARNING", "name_directory_mismatch", f, f"{name} != {f.parent.name}")
        if name in names:
            add("BLOCKER", "duplicate_skill_name", f, f"Also in {names[name]}")
        elif name:
            names[name] = rel
        if not fields.get("version"):
            add("WARNING", "missing_version", f, "Add a release version before listing")
        if not re.search(r"^##\s+(?:Verification|驗證|驗收|Tests?|Testing)\b", text, re.I | re.M):
            add("WARNING", "missing_verification", f, "No explicit verification section")
        if f.stat().st_size > 100 * 1024:
            add("WARNING", "very_large_skill", f, "Consider splitting long instructions into references")
        for code, pattern in CREDENTIALS:
            if pattern.search(text):
                add("BLOCKER", code, f, "Possible credential; inspect without publishing it")
        for code, pattern in RISK_PATTERNS:
            if pattern.search(text):
                add("WARNING", code, f, "Potentially unsafe instruction; review context")
        for dest in LOCAL_LINK.findall(text):
            if dest.startswith("/") or dest.startswith("~") or "://" in dest:
                continue
            link = (f.parent / dest).resolve()
            if not link.is_relative_to(root) or not link.exists():
                add("WARNING", "broken_local_link", f, dest)
        skills.append({"path": rel, "name": name, "description": description, "version": fields.get("version", "")})

    for f in sorted(root.iterdir()):
        if f.is_file() and (f.name in PRIVATE_ROOT_NAMES or f.suffix.lower() in PRIVATE_SUFFIXES):
            add("WARNING", "non_catalog_root_file", f, "Review before publishing; never include in a skill ZIP")
    levels = Counter(item["level"] for item in findings)
    codes = Counter(item["code"] for item in findings)
    return {"root": root.as_posix(), "skills": skills, "skill_count": len(skills),
            "summary": {"blockers": levels["BLOCKER"], "warnings": levels["WARNING"],
                        "by_code": dict(sorted(codes.items()))}, "findings": findings}


def report_markdown(result: dict) -> str:
    summary = result["summary"]
    lines = ["# Skill library audit", "",
             f"- Skills inspected: {result['skill_count']}",
             f"- Blockers: {summary['blockers']}",
             f"- Warnings: {summary['warnings']}", "",
             "## Findings", "",
             "| Level | Code | Path | Detail |", "| --- | --- | --- | --- |"]
    for f in result["findings"]:
        val = lambda x: str(x).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {f['level']} | {f['code']} | {val(f['path'])} | {val(f['detail'])} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument("--json", type=Path, help="Write complete machine-readable audit")
    p.add_argument("--markdown", type=Path, help="Write a human-readable report")
    p.add_argument("--fail-on-blockers", action="store_true", help="CI fails when blocking issues are found")
    args = p.parse_args(argv)
    result = scan(args.root)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(report_markdown(result), encoding="utf-8")
    for issue in result["findings"]:
        if issue["level"] == "BLOCKER":
            print(f"BLOCKER {issue['code']} {issue['path']}")
    print(f"SKILLS={result['skill_count']} BLOCKERS={result['summary']['blockers']} WARNINGS={result['summary']['warnings']}")
    print(json.dumps(result["summary"]["by_code"], ensure_ascii=False, sort_keys=True))
    return int(args.fail_on_blockers and result["summary"]["blockers"] > 0)


if __name__ == "__main__":
    sys.exit(main())
