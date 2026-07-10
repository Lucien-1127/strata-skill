# Monorepo: Add External Projects (Real Session Recipe)

This reference documents the exact commands used to add two external projects
(static brand-site + a Vite React Mini App) into a Git monorepo
(`zhiyan-mvp`). The source directories lived on the same host under
`/var/www/brand-site/` and `/home/ysga1/hermes-proxy-console/`.

## Setup

```bash
# Repo already cloned with remote configured
REPO=/home/ysga1/zhiyan-mvp-2
cd "$REPO"
git remote -v
# → origin  https://github.com/Lucien-1127/zhiyan-mvp.git
```

## Copy Steps

```bash
# 1) Brand site — exclude large/unwanted files
mkdir -p brand-site
cp -r /var/www/brand-site/* ./brand-site/
rm -rf ./brand-site/_ds
rm -f ./brand-site/pink-panther.mp4

# 2) Mini App — rsync with exclusions
mkdir -p mini-app
rsync -av --exclude=node_modules --exclude=dist \
  /home/ysga1/hermes-proxy-console/ ./mini-app/

# 3) Backend server + nginx config
mkdir -p mini-app/backend config
cp /usr/local/bin/miniapp-server.py ./mini-app/backend/
cp /etc/nginx/sites-available/brand-site ./config/nginx-brand-site.conf
```

## Submodule Trap Fix

The Mini App had its own `.git/` → `git add` tracked it as a **gitlink**:

```bash
# After initial commit: check for submodule entries
git status
# → "new file:   mini-app"  (this is a submodule pointer!)

# Fix:
git rm --cached mini-app                  # Remove submodule reference
rm -rf mini-app/.git                       # Remove embedded git dir
rsync -av --exclude=node_modules \
  --exclude=dist --exclude=.git \
  /home/ysga1/hermes-proxy-console/ ./mini-app/   # Re-copy clean
rm -f mini-app/.env                        # Remove potential secrets

# Stage real files and amend
git add -A
git commit --amend -m "feat: add brand-site + mini-app + nginx config"
git status
# → all files shown, no submodule entries
```

## Push (Non-Interactive)

```bash
# HTTPS push fails without TTY:
git push origin main
# → fatal: could not read Username for 'https://github.com': No such device

# Diagnose:
git config --list | grep -i "credential\|token\|gh_"
printenv | grep -i "GITHUB\|GH_\|GIT"
cat ~/.git-credentials 2>&1; cat ~/.netrc 2>&1

# Fix: ask user for PAT, then:
git remote set-url origin \
  https://Lucien-1127:<PAT>@github.com/Lucien-1127/zhiyan-mvp.git
git push origin main
```

## Verification

```bash
git branch -vv
git log origin/main..HEAD --oneline     # Should be empty
git status --short                       # Should be empty
```
