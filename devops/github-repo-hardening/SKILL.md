---
name: github-repo-hardening
description: "Pre-push audit: secrets, trash, git-config, license."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [GitHub, Security, Repo, Audit, QC]
status: active
---

# GitHub Repo Hardening — Pre-Push Audit

Pre-push audit that catches five classes of mistakes before they reach the remote: secrets in tracked files, oversized binaries in history, wrong git config, missing legal boilerplate, and garbage artifacts. Run this **before every git push** to a public repo.

Does NOT rewrite history (that is a manual, last-resort step). It flags problems; you fix them.

## When to Use

- "我要推上 GitHub，先檢查有沒有問題"
- "幫我掃這個 repo 有沒有不該 push 的東西"
- "檢查 git config 是否正確"
- "這個 repo 缺 LICENSE 嗎？"
- "有沒有敏感資料會上傳？"
- 任何 `git push` 到 public/origin 之前

## Prerequisites

- Local git repo with a remote configured.
- `search_files` / `terminal` tools available.

## How to Run

Run the audit script through the `terminal` tool against the target repo directory. Fix problems flagged as 🔴, review those flagged as 🟡.

## Quick Reference

| Check | What it catches | Severity |
|-------|----------------|----------|
| Secret scan | Real API keys (`sk-or-v1-`, `sk-ant-`, AWS `AKIA`), passwords, tokens in **tracked** files | 🔴 |
| Git email | Author email matches `lucien127@proton.me` (or user's real email) | 🟡 |
| Trash in tree | `.mp4`, `.db`, `.zip`, `.bak`, `__pycache__`, `.log`, `node_modules/`, `dist/`, `brand-site/` | 🔴 |
| Large blobs | Files >5MB in git history (use `git rev-list --objects`) | 🟡 |
| Missing boilerplate | `LICENSE`, `README.md`, `.gitignore` | 🟡 |
| Gitignore gaps | Missing `*.local`, `.env`, `__pycache__/`, `node_modules/`, `dist/` | 🟡 |

## Procedure

### Step 1 — Run the Audit Script

Invoke this audit script through the `terminal` tool:

```bash
bash /path/to/github-repo-hardening/scripts/pre-push-audit.sh /path/to/repo
```

If the script does not exist yet, paste the script from Step 5 and save it first.

### Step 2 — Interpret Results

The script outputs a structured report. Fix order:

1. **🔴 Secret leaks first** — `git rm --cached` the file, or `git filter-branch` if it is in history. Replace real values with placeholders.
2. **🔴 Trash in tree** — `git rm --cached` each file, update `.gitignore` to prevent re-adding.
3. **🟡 Git email** — `git config user.email "your@email.com"`
4. **🟡 Missing LICENSE/README/gitignore** — Create with `write_file`, `git add`, commit.
5. **🟡 Large blobs** — Investigate. If they should not be there, `git rm --cached`.
6. **🟡 Gitignore gaps** — Append missing patterns.

### Step 3 — Re-Audit After Fixes

Run the audit again after fixing. Only push when all 🔴 items are resolved.

### Step 4 — Push

```bash
git push origin <branch>
```

For history rewrites (filter-branch), use `--force` and confirm with the user.

## Pitfalls

- **sk-xxx / sk-YOUR_KEY / sk-... are NOT real secrets** — These are teaching placeholders. Only flag actual key patterns like `sk-or-v1-`, `sk-ant-`, `sess-`, or `freellmapi-<hex>`. The audit script must distinguish these.
- **git filter-branch rewrites every commit hash** — All collaborators must re-clone. Only use it for secrets that have been pushed. Prefer `git rm --cached` if the secret was only added in the latest commit.
- **Brand-site, dist/, build/ are build artifacts** — Add to `.gitignore`; do NOT `git rm` from working tree (use `--cached` to keep local copy).
- **Archived repos can still leak** — `git push` is blocked, but the history already on GitHub remains. For archival cleanup, un-archive → push fix → re-archive.
- **`.env.example` is safe** — It is a template. `.env` (no suffix) is the one that must be gitignored.
- **MP4 files in `media-pipeline/scripts/output/` are generated** — Exclude the entire `output/` directory, not individual files.
- **The QC_Phase1_Report.md is ephemeral** — Save useful parts as a skill (this one), not as a file that will be stale in a week.

## Verification

```bash
bash pre-push-audit.sh /path/to/repo
# Expected: "🔴 SECRET LEAKS: 0 | 🔴 TRASH TRACKED: 0 | ✅ All high-priority checks pass"
```
