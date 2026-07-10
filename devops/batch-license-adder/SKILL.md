---
name: batch-license-adder
description: Batch-add LICENSE files (MIT) to multiple GitHub repos — local clones and remote-only repos — with pre-commit security scanning and divergence handling.
version: 0.1.0
author: Hermes
platforms: [linux]
tags:
  - Git
  - GitHub
  - License
  - Batch
  - Compliance
status: stable
---

# Batch License Adder

Add MIT License files to a fleet of GitHub repos. Handles both repos that already have local clones and repos that must be cloned remotely. Runs a security scan (`api_key`, `token`, `password`, `sk-`, `AKIA`, `-----BEGIN`) before every commit, and handles push-rejected divergence with rebase.

## When to Use

- User says "幫所有 repo 補上 LICENSE" / "add MIT License to all repos"
- User provides a list of repos (some local, some remote-only)
- Preparing repos for open-source release
- Compliance sweep across multiple projects

## Prerequisites

- SSH keys configured and authenticated (`ssh -T git@github.com` returns success)
- `git config user.name` and `git config user.email` set globally — or set per-repo clone
- Repos belong to the same GitHub user/org (or you have SSH access to all)

## Standard MIT License Template

```text
MIT License

Copyright (c) 2026 Lucien

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Procedure

### Phase 1 — Inventory & Categorize

1. **Get the repo list from the user.** Each entry should include:
   - Repo name
   - Remote URL (SSH: `git@github.com:<user>/<repo>.git`)
   - Local path (if already cloned)
   - Any skip instructions (e.g. zhiyan-legal already has LICENSE)

2. **Check each local repo has `.git`:**
   ```bash
   ls -la <path>/.git 2>&1
   ```

3. **Verify SSH access** to all remotes:
   ```bash
   git ls-remote git@github.com:<user>/<repo>.git 2>&1 | head -5
   ```

4. **Check which repos already have a LICENSE file:**
   ```bash
   ls <path>/LICENSE* 2>&1
   ```

### Phase 2 — Security Scan

Run on EVERY repo before writing the LICENSE file:

```bash
grep -rn -E 'api_key|token|password|sk-|AKIA|-----BEGIN' \
  --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' \
  --include='*.env' --include='*.txt' --include='*.cfg' --include='*.ini' \
  --include='*.md' --include='*.js' --include='*.ts' --include='*.env*' \
  . 2>/dev/null || echo "No sensitive data found"
```

- If results contain **actual secrets** (not just variable names or docs), **skip the repo** and flag it.
- If results are only code-level references (`api_key=os.getenv(...)`, doc strings mentioning `token`), the repo is clean — proceed.

### Phase 3 — Write & Push

**For local clones:**

```bash
cd <path>
git pull --rebase origin main 2>&1   # Sync first to avoid push rejection
# (Alternative: check if push will work first — try push, only pull on reject)
write_file(path="<path>/LICENSE", content="<MIT License text>")
git add LICENSE
git commit -m "Add MIT License"
git push origin main
```

If push is rejected (`fetch first`):
```bash
git pull --rebase origin main
git push origin main
```

**For remote-only repos:**

```bash
mkdir -p /tmp/license-work
git clone git@github.com:<user>/<repo>.git /tmp/license-work/<repo>
cd /tmp/license-work/<repo>
git config user.name "Lucien"
git config user.email "lucien127@proton.me"
# Security scan first
# Then write LICENSE, commit, push
git add LICENSE && git commit -m "Add MIT License"
git push origin main
```

### Phase 4 — Handle Multi-Branch Repos

Check if the repo has multiple branches:

```bash
git branch -a
```

If yes, determine the default branch (`remotes/origin/HEAD -> origin/<branch>`). Write LICENSE to each non-default branch too:

```bash
git checkout <other-branch>
# Write LICENSE if missing
git add LICENSE && git commit -m "Add MIT License"
git push origin <other-branch>
```

### Phase 5 — Cleanup

```bash
rm -rf /tmp/license-work
```

## Pitfalls

- **Default branch not `main`**: Check with `git remote show origin | grep HEAD` or `git branch -a` for `remotes/origin/HEAD -> origin/<branch>`. Adjust push target accordingly.
- **Diverged branches**: If `git pull --rebase` fails with "cannot rebase: You have unstaged changes", stash first, rebase, then pop. But note: stash+rebase drops the LICENSE commit if you already committed locally — re-write it after.
- **Non-main branches needing LICENSE**: `hermes-lucian` type repos may have an active feature branch (`claude/*`, `develop`) that should also get the LICENSE. Always check `git branch -a`.
- **Already has LICENSE**: Some repos may already have one (e.g. `thai-zh-pwa` had `chore: add README.md, .gitignore, and LICENSE`). Detect early with `ls LICENSE*` or check `git log --oneline | grep -i license`.
- **SSH vs HTTPS remote URLs**: Some cloned repos may use HTTPS (`https://github.com/...`). Convert to SSH for non-interactive push: `git remote set-url origin git@github.com:<user>/<repo>.git`.
- **Temp clone cleanup**: Always `rm -rf /tmp/license-work` when done. The CWD may be inside the deleted dir — wrap in `cd /tmp` first or ignore the harmless `getcwd` error.
- **The security scan pattern above catches legitimate code tokens** (variable names, doc comments). Distinguish between:
  - ❌ **Real secrets**: `api_key="sk-or-v1-abc123..."`, `password="hunter2"`, `-----BEGIN RSA PRIVATE KEY-----`
  - ✅ **Code references**: `api_key=os.getenv("API_KEY")`, docstrings like `max_tokens: int = 4096`, examples like `client = OpenAI(api_key="EMPTY")`

## Verification

Confirm each repo's LICENSE commit exists on GitHub:

```bash
# From local clone:
git log --oneline -3

# For remote-only — inspect via:
git ls-remote git@github.com:<user>/<repo>.git refs/heads/main
# Then check file exists with curl or browser
```
