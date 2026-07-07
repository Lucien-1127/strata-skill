# Bulk Fix: Frontmatter Description = Skill Name

## Problem

75 skills (62.5% of the library, as of 2026-07-07) have `description: <skill-name>` in their YAML frontmatter — meaning the `skills_list()` API returns a useless description even though the body contains real content.

All 75 share the exact same pattern:

```yaml
---
name: skill-name
description: skill-name    # ← never updated from default
---
```

while the body has a real description in `## 📖 Description`.

## Root Cause

Bulk import from external prompt systems (GitHub Copilot prompts, knowledge base files, legacy agent prompts). The import script populated the body content faithfully but never updated the frontmatter `description` field.

## Automated Fix Strategy

Run a Python script that:

1. Scans all `~/.hermes/skills/**/SKILL.md` files
2. For each file where `description` in YAML frontmatter equals `name` (case-insensitive, strip hyphens):
3. Extract the first non-empty paragraph from `## 📖 Description` (markdown body section)
4. Patch the frontmatter `description:` field with that text
5. If body description is also empty (like `gcp-cost-optimization`), extract from the first `#` heading after the frontmatter

## Script

```python
#!/usr/bin/env python3
"""Bulk-fix frontmatter description = name in Hermes SKILL.md files."""

import os, re, glob

def normalize(s):
    """Normalize for comparison: lowercase, remove hyphens/underscores/punctuation."""
    return re.sub(r'[^a-z0-9]', '', s.lower().strip())

for path in glob.glob(os.path.expanduser("~/.hermes/skills/**/SKILL.md"), recursive=True):
    with open(path) as f:
        text = f.read()

    # Extract frontmatter
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        continue
    fm = m.group(1)

    # Check if description == name
    name_m = re.search(r'^name:\s*["\']?([\w-]+)', fm, re.M)
    desc_m = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
    if not name_m or not desc_m:
        continue

    name = name_m.group(1)
    desc = desc_m.group(1)
    if normalize(desc) != normalize(name):
        continue  # already has a meaningful description

    # Extract body description from ## 📖 Description section
    body_desc = ""
    body_m = re.search(r'## 📖 Description\s*\n+\s*(.+?)\s*\n', text, re.DOTALL)
    if body_m:
        candidate = body_m.group(1).strip()
        # Skip empty YAML block scalars like `>-`
        if candidate and candidate != '>-':
            body_desc = candidate

    # Fallback: first # heading after frontmatter
    if not body_desc:
        after_fm = text[m.end():]
        h1 = re.search(r'^#\s+(.+?)\s*$', after_fm, re.M)
        if h1:
            body_desc = h1.group(1).strip()

    if not body_desc:
        print(f"⚠️ SKIP (no body desc found): {path}")
        continue

    # Escape for YAML single-line string
    yaml_desc = body_desc.replace('"', '\\"').strip()
    
    # Patch description line in frontmatter
    old_line = desc_m.group(0)
    new_line = f'description: "{yaml_desc}"'
    new_text = text.replace(old_line, new_line, 1)

    if new_text == text:
        print(f"❌ FAILED: {path}")
        continue

    with open(path, 'w') as f:
        f.write(new_text)
    print(f"✅ FIXED: {path}  →  \"{yaml_desc}\"")
```

## Manual Fallback

If the script approach isn't available (e.g., read-only environment), each skill can be fixed individually via `skill_manage(action='patch')`:

```bash
# Pattern: replace frontmatter description line
# old_string: "description: <skill-name>"
# new_string: 'description: "<real description pulled from body>"'
```

## Affected Skills (2026-07-07 Audit)

See the audit report at `/home/ysga1/hermes-skills-description-audit-2026-07-07.md` for the full list of 75 skills and their corresponding body descriptions.
