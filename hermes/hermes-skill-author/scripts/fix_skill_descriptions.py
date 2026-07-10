#!/usr/bin/env python3
"""
Batch-fix Hermes skills where frontmatter description == skill name.

Reads each SKILL.md, checks if description matches name, and if so,
replaces it with the first non-empty paragraph from the body's
## 📖 Description section. Falls back to the first # heading.

Usage:
  python3 fix_skill_descriptions.py                    # run the fix
  python3 fix_skill_descriptions.py --dry-run           # preview only
  python3 fix_skill_descriptions.py --status            # count remaining
  python3 fix_skill_descriptions.py --from-csv file.csv # use CSV mapping
"""

import os, re, glob, sys

BASE = os.path.expanduser("~/.hermes/skills")

def normalize(s):
    """Lowercase + strip all non-alphanumeric chars for comparison."""
    return re.sub(r'[^a-z0-9]', '', s.lower().strip())

def find_skills():
    """Find all SKILL.md files and return (path, frontmatter, body, name, desc)."""
    results = []
    for path in glob.glob(os.path.join(BASE, "**/SKILL.md"), recursive=True):
        with open(path) as f:
            text = f.read()
        # Extract frontmatter
        m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        body = text[m.end():]

        name_m = re.search(r'^name:\s*["\']?([\w-]+)', fm, re.M)
        desc_m = re.search(r'^description:\s*["\']?(.+?)(["\'])?\s*$', fm, re.M)
        if not name_m or not desc_m:
            continue

        results.append({
            "path": path,
            "fm": fm,
            "body": body,
            "full_text": text,
            "name": name_m.group(1),
            "desc_raw": desc_m.group(1),
            "desc_line": desc_m.group(0),
            "needs_fix": normalize(desc_m.group(1)) == normalize(name_m.group(1))
        })
    return results

def extract_body_description(body_text):
    """Extract first paragraph from ## 📖 Description section."""
    m = re.search(r'## 📖 Description\s*\n+\s*(.+?)\s*\n', body_text, re.DOTALL)
    if m:
        cand = m.group(1).strip()
        if cand and cand != '>-':
            return cand
    return ""

def extract_fallback_desc(body_text):
    """Fallback: first # heading after frontmatter."""
    m = re.search(r'^#\s+(.+?)\s*$', body_text, re.M)
    if m:
        return m.group(1).strip()
    return ""

def csv_line_for(skill):
    """Format as CSV row for manual mapping."""
    safe_name = skill["name"].replace('"', '""')
    safe_desc = extract_body_description(skill["body"])
    if not safe_desc:
        safe_desc = extract_fallback_desc(skill["body"])
    if not safe_desc:
        safe_desc = "(empty)"
    safe_desc = safe_desc.replace('"', '""')
    return f'"{safe_name}","{safe_desc}"'


def main():
    dry_run = "--dry-run" in sys.argv
    show_status = "--status" in sys.argv
    from_csv = None
    for i, a in enumerate(sys.argv):
        if a == "--from-csv" and i+1 < len(sys.argv):
            from_csv = sys.argv[i+1]

    skills = find_skills()

    if show_status:
        bad = [s for s in skills if s["needs_fix"]]
        good = [s for s in skills if not s["needs_fix"]]
        print(f"Total skills: {len(skills)}")
        print(f"Good descriptions: {len(good)}")
        print(f"Need fix: {len(bad)}")
        if bad:
            print("\nStill broken:")
            for s in bad:
                print(f"  ❌ {s['name']}")
        return

    if from_csv:
        # Load CSV mapping
        import csv
        mapping = {}
        with open(from_csv, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    mapping[row[0].strip()] = row[1].strip()
    else:
        mapping = {}  # auto-detect from body

    fixed = 0
    skipped = 0
    for s in skills:
        if not s["needs_fix"]:
            continue

        # Determine new description
        if from_csv:
            new_desc = mapping.get(s["name"], "")
        else:
            new_desc = extract_body_description(s["body"])
            if not new_desc:
                new_desc = extract_fallback_desc(s["body"])

        if not new_desc:
            print(f"⚠️  SKIP (no description found): {s['name']}  [{s['path']}]")
            skipped += 1
            continue

        # Escape for YAML
        yaml_desc = new_desc.replace('"', '\\"').strip()

        old_line = s["desc_line"]
        new_line = f'description: "{yaml_desc}"'
        new_text = s["full_text"].replace(old_line, new_line, 1)

        if new_text == s["full_text"]:
            print(f"❌  FAIL: {s['name']} — replacement had no effect")
            skipped += 1
            continue

        if dry_run:
            print(f"🔍  WOULD FIX: {s['name']}  →  \"{yaml_desc}\"")
        else:
            with open(s["path"], 'w') as f:
                f.write(new_text)
            print(f"✅  FIXED: {s['name']}  →  \"{yaml_desc}\"")
        fixed += 1

    print(f"\nDone: {fixed} fixed, {skipped} skipped")

    if dry_run and not from_csv:
        # Also print CSV for manual editing
        print("\n--- CSV for manual mapping ---")
        print('"name","description"')
        for s in skills:
            if s["needs_fix"]:
                print(csv_line_for(s))


if __name__ == "__main__":
    main()
