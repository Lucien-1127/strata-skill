# Batch License Adder — Worked Example

This file documents a real session where 6 repos (4 local, 2 remote-only) received MIT License files.

## Repo Inventory

| Repo | Type | Outcome |
|------|------|---------|
| CineAgent | Local clone at `~/CineAgent` | ✅ `8f19f76` pushed to main |
| zhiyan-mvp | Local clone at `~/zhiyan-mvp-2` | ✅ `4650229` pushed to main |
| hermes-skills | Local clone at `~/hermes-skills` | ✅ `fc0a8c5` pushed to main |
| lucian-station | Remote-only → cloned to `/tmp/` | ✅ `0297f57` pushed to main |
| hermes-lucian | Remote-only → cloned to `/tmp/` | ✅ 2 branches: `6bdc3c0` (main), `77b3bb4` (claude/legal-system-research-xbxq53) |
| thai-zh-pwa | Remote-only → cloned to `/tmp/` | ⏭️ Already had LICENSE (commit `5ece684`) |
| strata-skill | In `~/.hermes/skills` | ⏭️ Skipped per instructions |
| zhiyan-legal | — | ⏭️ Skipped per instructions (already had LICENSE) |

## Divergence Handled

- **CineAgent**: Remote had 2 new commits ahead of local. `git push` rejected. Solution:
  1. `git pull --rebase origin main` — but failed with "unstaged changes"
  2. `git stash` → `git rebase origin/main` → `git stash pop`
  3. This dropped the LICENSE commit from the rebase — but `git log` showed it was still present (rebased on top)
  4. `git push origin main` succeeded
  *(Lesson: stash+rebase on a repo that already committed locally will rebase that commit too — verify with `git log` before re-creating)*

- **hermes-skills**: Remote had commits ahead. Simple `git pull --rebase origin main` then `git push` worked.

- **hermes-lucian**: Default branch was `claude/legal-system-research-xbxq53` (not `main`). After cloning, checked out `main` separately and wrote LICENSE there too.

## Security Scan Pattern Used

```bash
grep -rn -E 'api_key|token|password|sk-|AKIA|-----BEGIN' \
  --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' \
  --include='*.env' --include='*.txt' --include='*.cfg' --include='*.ini' \
  --include='*.md' --include='*.js' --include='*.ts' --include='*.env*' \
  . 2>/dev/null || echo "No sensitive data found"
```

All repos passed cleanly. Matches were all code-level references (variable names, docstrings, `.env.example` placeholders), not actual secrets.

## SSH Remote URL Fix

`hermes-skills` was initially cloned with HTTPS. Fixed with:
```bash
git remote set-url origin git@github.com:Lucien-1127/hermes-skills.git
```

## Temp Cleanup

```bash
rm -rf /tmp/license-work
```
