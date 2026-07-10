---
name: git-sync-workflow
description: Sync local git repo with remote origin.
version: 0.2.0
author: Hermes
platforms: [linux]
tags:
  - Git
  - GitHub
  - Sync
  - Workflow
status: stable
---

# Git Sync Workflow

Reconcile a local git branch with its remote (`origin/main`), handling
rejected pushes due to remote-ahead divergence. Covers the full cycle:
status check → fetch → rebase → verify → push. Does **not** handle merge
conflict resolution (manual step if conflicts appear).

## When to Use

- User says "同步 GitHub" / "sync with GitHub" / "更新遠端"
- User says "幫我 push" or "確認 GitHub 狀態"
- `git push` is rejected with "fetch first"
- After making local changes, confirming both directions are in sync
- Regular maintenance check before a deploy or release

## Prerequisites

- Git installed and configured
- Remote `origin` set (`git remote -v` to verify)
- SSH keys or HTTPS credentials already configured
- Working directory is the project root
- **Push authentication**: In non-interactive environments (SSH sessions, CI, agent tooling), `git push` over HTTPS will fail if no credential helper is configured. See [Credential Diagnostics](#credential-diagnostics) below for troubleshooting.

## How to Run

Invoke each step through the `terminal` tool inside the project directory:

```bash
terminal(command="cd <project> && git status")
terminal(command="cd <project> && git fetch origin")
terminal(command="cd <project> && git pull --rebase origin <branch>")
terminal(command="cd <project> && git push origin <branch>")
```

## Quick Reference

| Step | Command | Purpose |
|------|---------|---------|
| Status | `git status` | Confirm working tree clean |
| Fetch | `git fetch origin` | See remote changes without merging |
| Log diff | `git log HEAD..origin/main --oneline` | List commits we're behind |
| Rebase | `git pull --rebase origin main` | Fast-forward integrate remote changes |
| Verify | `git branch -vv` | Confirm local tracks remote at same hash |
| Push | `git push origin main` | Publish local commits |
| Confirm | `git log origin/main..HEAD --oneline` | Empty = fully in sync |

## Procedure

1. **Check working tree status**
   ```bash
   git status
   ```
   Must be clean. If not, commit or stash first.

2. **Try a push** (fast path — local may already be ahead or equal)
   ```bash
   git push origin <branch>
   ```
   - ✅ Success → done. Skip to step 7 to verify.
   - ❌ Rejected (`fetch first`) → continue below.

3. **Fetch remote changes**
   ```bash
   git fetch origin
   ```

4. **Review what's new remotely**
   ```bash
   git log HEAD..origin/main --oneline
   ```
   Inspect the commit list to assess scope before merging.

5. **Pull with rebase** (keeps history linear)
   ```bash
   git pull --rebase origin <branch>
   ```
   Conflicts surface here. If they do, stop and report which files conflict.

6. **Push local commits** (all reconciled commits + any local-only ones)
   ```bash
   git push origin <branch>
   ```

7. **Final verification — three checks**
   ```bash
   git branch -vv
   git log origin/main..HEAD --oneline
   git status --short
   ```
   Expected: branch shows `[origin/main]`, log output is **empty** (nothing ahead of origin), status is **empty** (clean tree).

## Credential Diagnostics

When `git push` fails with `could not read Username for 'https://github.com': No such device or address` (no TTY), diagnose in order:

1. **Check git config** — `git config --list | grep -i "credential\|token\|gh_"` — for an existing credential helper
2. **Check environment variables** — `printenv | grep -i "GITHUB\|GH_\|GIT"` — for `GITHUB_TOKEN` or `GH_TOKEN`
3. **Check credential files** — `cat ~/.git-credentials 2>&1; cat ~/.netrc 2>&1`
4. If none found, ask the user for a GitHub Personal Access Token (classic, `repo` scope) and set the remote URL inline:
   ```bash
   git remote set-url origin https://<user>:<token>@github.com/<user>/<repo>.git
   git push origin <branch>
   ```
5. Once pushed, recommend they configure a credential helper (`git config --global credential.helper store` or `cache`) for future non-interactive pushes.

## Pitfalls

- **Uncommitted changes** block pull/rebase. Always run `git status` first.
- **Merge conflicts** can appear during `pull --rebase`. This skill does not cover resolution — report the conflicting files.
- **Force-pushed remotes** (rebased or amended history upstream) will be rejected. Use `git fetch --force` only when you understand the consequences.
- **Default branch not `main`**: adjust the branch name (e.g. `master`, `develop`).
- **Multiple remotes**: this skill assumes a single `origin`. Forks need a different remote name.
- **Large repos**: `git fetch` may take 30+ seconds. Set `timeout` generously (60s).
- **Skills-repo whitelist `.gitignore` trap**: When syncing `~/.hermes/skills/` to a version-controlled repo (e.g. `strata-skill`), a **whitelist-style `.gitignore`** (explicitly listing every tracked skill) silently excludes newly created skills from `git add`. Diagnosis: `git status --short` shows far fewer files than `find skills -type d | wc -l`. Fix: replace whitelist with a **blacklist** `.gitignore` that only excludes non-skill artifacts (`.git/`, `.usage.json`, `.archive/`, `__pycache__/`, `*.pyc`, OS files). After switching from whitelist to blacklist, expect 3-10× more files tracked (e.g. 33→348). Always verify with `git ls-files | wc -l` after the initial blacklist add.
- **Embedded .git directory → submodule tracking**: When you `cp -r` or `rsync` a project into a monorepo and the source still has a `.git/` directory, `git add` tracks it as a **gitlink (submodule)** instead of regular files (mode `160000`). Fix:
  1. Remove the submodule reference: `git rm --cached <dir>`
  2. Delete the embedded `.git`: `rm -rf <dir>/.git`
  3. Re-copy the source files (excluding `.git`): `rsync -av --exclude=.git <source>/ <dir>/`
  4. Re-add: `git add -A`
  5. Amend the previous commit if already committed: `git commit --amend`
  6. Verify: `git status` shows no submodule references, `git ls-files --stage <dir>/` shows mode `100644` (files) not `160000` (gitlink)
- **Push fails "could not read Username" (no TTY)**: See [Credential Diagnostics](#credential-diagnostics) above. Do NOT assume SSH is configured — check first.

## Verification

One-shot confirmation:

```bash
git branch -vv && git log origin/main..HEAD --oneline && git status --short
```

Expected output:
- `* main <hash> [origin/main] <message>` (tracking up to date)
- Empty log line (no commits ahead)
- Empty status line (clean working tree)

## Linked References

- `references/monorepo-add-external-project.md` — Full worked example of adding external projects (brand-site, Vite React Mini App) into a monorepo, including the embedded-.git submodule trap fix and non-interactive push credential diagnostics.
- `templates/skills-repo-gitignore.txt` — Blacklist-style `.gitignore` for `~/.hermes/skills/` repos (avoids the whitelist trap that silently excludes new skills).
