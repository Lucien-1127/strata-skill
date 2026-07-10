---
name: github-repo-overhaul
description: "Audit, secure, and standardize all GitHub repos."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [GitHub, Repo, Cleanup, Batch, Standardize]
status: active
---

# GitHub Repo Overhaul — Batch Standardization

Audit all of a user's GitHub repos, then batch-fix every common gap: missing LICENSE, README, .gitignore, empty topics/descriptions, wrong git email, garbage files in tracking, secret leaks, and stale repos. Runs in parallel where possible and finishes with a QC gate before the final push.

Does NOT handle org-level settings, branch protection, or CI/CD config. It standardizes the repo surface — not the development workflow inside them.

## When to Use

- "幫我把所有 GitHub repo 整理一遍"
- "檢查所有 repo 有無缺 LICENSE/README"
- "批量補 topics 和 description"
- "掃描所有 repo 有沒有金鑰洩漏"
- "把舊 repo archive 掉"
- "清理每個 repo 的 git history"

## Prerequisites

- `curl` and `python3` available on the system.
- GitHub PAT (classic `public_repo` scope, or fine-grained with `administration:write` + `metadata:write`) for write operations. Read-only checks can run without one, but writes (topics, archive, create repo) require it.
- SSH key configured for git pushes (`git@github.com`).
- Local clones of repos that need content changes (LICENSE, README, .gitignore).

## How to Run

Dispatch via `delegate_task`: one subagent for discovery, parallel subagents for each fix category (license, topics, trash cleanup, archive), then one for final QC verification.

## Quick Reference

| Phase | Task | Parallel |
|-------|------|----------|
| 1 | Discover all repos via API | Single |
| 2 | Add MIT License | Per-repo (parallel) |
| 3 | Add topics + descriptions | Per-repo (parallel) |
| 4 | Fix .gitignore + README | Per-repo (parallel) |
| 5 | Remove trash from tracking | Per-repo (parallel) |
| 6 | Redact secret leaks | Per-repo (parallel) |
| 7 | Archive stale repos | Per-repo (parallel) |
| 8 | QC verification | Single |

## Procedure

### Phase 1 — Discover All Repos

Use the GitHub API to list every repo, their current description, topics, LICENSE status, README status, and archival state:

```bash
# List all repos with metadata
curl -s "https://api.github.com/users/<owner>/repos?per_page=100"
```

Parse into a structured table. Key fields: `name`, `description`, `language`, `visibility`, `archived`, `size`, `default_branch`.

Classify each repo:
- **Active**: actively developed, needs full treatment
- **Stale**: can be archived after LICENSE/README patch
- **Transient**: one-off experiments or duplicates

### Phase 2 — Batch MIT License (Parallel)

For every repo missing a LICENSE, do one of:
1. **Local clone exists**: `cd ~/repo && write_file LICENSE (MIT content) && git add && git commit && git push`
2. **Remote only**: `git clone` to `/tmp/`, add LICENSE, push, delete temp

Skip if the repo already has a LICENSE (verify via API, not local check).

Standard MIT License content:
```
MIT License

Copyright (c) 2026 Lucien

Permission is hereby granted...
```

### Phase 3 — Topics + Descriptions (Parallel, Requires PAT)

Use the GitHub REST API:

```bash
# Update description
curl -X PATCH -H "Authorization: Bearer $PAT" \
  "https://api.github.com/repos/$OWNER/$REPO" \
  -d '{"description": "..."}'

# Update topics
curl -X PUT -H "Authorization: Bearer $PAT" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  "https://api.github.com/repos/$OWNER/$REPO/topics" \
  -d '{"names": ["tag1", "tag2", "..."]}'
```

Topics should be lowercase, no spaces, and match the repo's actual content domain. Aim for 3–7 topics per repo.

### Phase 4 — README + .gitignore (Parallel)

For repos missing README.md:
1. Write a zh-TW README with: project name, 1-line intro, features, tech stack, install/usage, license note
2. For generated repos (Vite defaults, etc.): replace the template content entirely

For repos with weak .gitignore:
```
node_modules/
dist/
build/
.env
.env.local
*.local
__pycache__/
*.pyc
*.pyo
*.log
*.db
*.sqlite
.DS_Store
Thumbs.db
*.swp
*.swo
*~
```

### Phase 5 — Remove Trash from Tracking (Parallel)

Scan tracked files for these patterns and `git rm --cached` (keep local, remove from git):

| Pattern | Reason |
|---------|--------|
| `*.mp4`, `*.mov` | Generated video output |
| `*.db`, `*.sqlite` | Runtime databases |
| `*.bak`, `*.backup` | Backup artifacts |
| `*.zip`, `*.tar.gz` | Large archives |
| `*.log` | Runtime logs |
| `__pycache__/` | Python bytecode cache |
| `node_modules/` | NPM dependencies |
| `dist/`, `build/`, `.next/` | Build artifacts |
| `brand-site/` | Brand/build output directory |
| `.hub/`, `.osf/` | Tool hub caches |

After removal, add these patterns to `.gitignore`.

### Phase 6 — Redact Secret Leaks (Parallel)

Scan tracked files for **real** key patterns (NOT teaching placeholders like `sk-xxx`):

```
sk-or-v1-[A-Za-z0-9]{20,}    # OpenRouter
sk-ant-[A-Za-z0-9]{20,}      # Anthropic
sk-proj-[A-Za-z0-9]{20,}     # OpenAI project
sess-[A-Za-z0-9]{20,}        # OpenAI session
AKIA[0-9A-Z]{16}             # AWS
freellmapi-[A-Za-z0-9]{10,}  # FreeLLM API
-----BEGIN (RSA|OPENSSH|PRIVATE|EC) KEY-----  # Private keys
```

For each match:
1. `patch` the file to replace the real key with `<redacted-placeholder>`
2. Commit
3. If the file was already pushed, use `git filter-branch` to purge it from history (last resort — force push)

### Phase 7 — Archive Stale Repos (Requires PAT)

```bash
curl -X PATCH -H "Authorization: Bearer $PAT" \
  "https://api.github.com/repos/$OWNER/$REPO" \
  -d '{"archived": true}'
```

Candidates for archival: duplicates of current repos, Claude Code generation artifacts, unused experiments, prototype repos with no commits in >30 days.

### Phase 8 — QC Verification

After all fixes, run a final audit on every repo:

| Check | Method |
|-------|--------|
| LICENSE exists | API `contents/LICENSE` |
| README exists | API `contents/README.md` |
| .gitignore complete | Local scan or API |
| Topics exist | API `topics` endpoint |
| Description set | API `description` field |
| No real secrets | `search_files` for key patterns |
| No trash tracked | `git ls-files` filtered |
| Correct git email | `git config user.email` |
| Archived status | API `archived` field |

## Pitfalls

- **API rate limits hit hard on 10+ repos** — Use authenticated requests (PAT) for all API calls to get 5000/hr instead of 60/hr.
- **Archived repos block push** — Un-archive → fix → re-archive if you need to patch an archived repo.
- **git filter-branch is destructive** — It rewrites every commit SHA. All collaborators must re-clone. Only use it for secrets that have been pushed. Prefer `git rm --cached` if the secret was only added in the latest commit.
- **PAT must be cleaned up** — The PAT appears in bash history and tool output. After use: `history -c`, unset env vars, delete the token in GitHub settings.
- **sk-xxx / sk-YOUR_KEY / sk-... are NOT real secrets** — These are teaching placeholders in docs. The audit script must distinguish them from real key patterns.
- **Topics need lowercase, no spaces** — GitHub rejects topics with uppercase or spaces.
- **Descriptions have a 120-char limit on GitHub** — Keep them concise.
- **Parallel subagents share no state** — Each one needs the full context: PAT, owner, repo list, target descriptions/topics. Re-pass context even if it feels redundant.
- **Batch topics update via API requires Accept header** — The topics endpoint needs `application/vnd.github.mercy-preview+json` or it returns 404.

## Verification

```bash
# Final state check for any repo
curl -s "https://api.github.com/repos/$OWNER/$REPO" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  print(f'README: {\"✅\" if d.get(\"has_readme\") else \"❌\"}'); \
  print(f'License: {d.get(\"license\",{}).get(\"spdx_id\",\"❌\")}'); \
  print(f'Archived: {d.get(\"archived\")}'); \
  print(f'Topics: {d.get(\"topics\",[])}')"
```
