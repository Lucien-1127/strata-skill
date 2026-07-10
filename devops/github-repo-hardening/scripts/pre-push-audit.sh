#!/usr/bin/env bash
# Pre-push audit script — github-repo-hardening skill
# Usage: bash pre-push-audit.sh [path-to-repo]
# If no path given, uses current directory.

set -e

REPO="${1:-.}"
cd "$REPO"

if [ ! -d ".git" ]; then
  echo "❌ Not a git repository: $REPO"
  exit 1
fi

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

SECRET_LEAKS=0
TRASH_TRACKED=0
ISSUES=0

echo "============================================"
echo "🔍 GitHub Repo Pre-Push Audit"
echo "Repo: $(basename $(git rev-parse --show-toplevel))"
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Email: $(git config user.email)"
echo "============================================"
echo ""

# ── 1. Secret scan (tracked files only) ──
echo "--- 🔴 1. Secret scan (tracked files) ---"
# Real key patterns (NOT sk-xxx / sk-YOUR_KEY placeholders)
REAL_KEY_PATTERNS=(
  'sk-or-v1-[A-Za-z0-9]{20,}'
  'sk-ant-[A-Za-z0-9]{20,}'
  'sk-proj-[A-Za-z0-9]{20,}'
  'sess-[A-Za-z0-9]{20,}'
  'AKIA[0-9A-Z]{16}'
  'freellmapi-[A-Za-z0-9]{10,}'
  '-----BEGIN (RSA|OPENSSH|PRIVATE|EC) KEY-----'
)

EXCLUDE_PATTERNS='sk-xxx|sk-YOUR_KEY|sk-\.\.\.|sk-dummy'

for pattern in "${REAL_KEY_PATTERNS[@]}"; do
  results=$(git ls-files -z | xargs -0 -I{} sh -c '
    if [ -f "{}" ]; then
      grep -n "'"$pattern"'" "{}" 2>/dev/null | grep -vi "'"$EXCLUDE_PATTERNS"'" | head -3 | while read line; do
        echo "  {}:$line"
      done
    fi
  ')
  if [ -n "$results" ]; then
    echo -e "${RED}⚠️  Real key pattern '$pattern' found:${NC}"
    echo "$results"
    SECRET_LEAKS=$((SECRET_LEAKS + 1))
  fi
done

if [ "$SECRET_LEAKS" -eq 0 ]; then
  echo -e "${GREEN}✅ No real secret keys in tracked files${NC}"
fi
echo ""

# ── 2. Trash tracked (files that should be gitignored) ──
echo "--- 🔴 2. Trash tracked in git tree ---"
TRASH_PATTERNS='\.mp4$|\.db$|\.sqlite$|\.bak$|\.log$|\.zip$|\.tar\.gz$|__pycache__|node_modules/|dist/|build/|\.next/|brand-site/|\.hub/|\.osf/'
trash_files=$(git ls-files | grep -E "$TRASH_PATTERNS" | head -10)
if [ -n "$trash_files" ]; then
  echo -e "${RED}⚠️  Trash files tracked:${NC}"
  echo "$trash_files"
  TRASH_TRACKED=$((TRASH_TRACKED + $(echo "$trash_files" | wc -l)))
fi

# Check large files (>5MB) in current tree
large_files=$(git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && test "$(stat -c%s "{}")" -gt 5242880 && echo "  {} ($(du -h "{}" | cut -f1))"' 2>/dev/null)
if [ -n "$large_files" ]; then
  echo -e "${YELLOW}⚠️  Large files tracked (>5MB):${NC}"
  echo "$large_files"
  ISSUES=$((ISSUES + 1))
fi

# Check large files in git history
large_history=$(git rev-list --objects --all 2>/dev/null | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' 2>/dev/null | awk '/^blob/ {print substr($0,6)}' | sort -rn -k2 | head -5 | awk '{print $3, $2/1024/1024 " MB"}' 2>/dev/null || true)
if [ -n "$large_history" ]; then
  echo -e "${YELLOW}⚠️  Largest blobs in git history:${NC}"
  echo "$large_history"
  ISSUES=$((ISSUES + 1))
fi

if [ "$TRASH_TRACKED" -eq 0 ]; then
  echo -e "${GREEN}✅ No trash tracked in git tree${NC}"
fi
echo ""

# ── 3. Git config check ──
echo "--- 🟡 3. Git config ---"
email=$(git config user.email 2>/dev/null)
name=$(git config user.name 2>/dev/null)
echo "  Email: $email"
echo "  Name:  $name"
if echo "$email" | grep -qi "nousresearch\|localhost\|anonymous"; then
  echo -e "${RED}⚠️  Wrong git email — should be your GitHub email${NC}"
  ISSUES=$((ISSUES + 1))
else
  echo -e "${GREEN}✅ Git email looks OK${NC}"
fi
echo ""

# ── 4. Missing boilerplate ──
echo "--- 🟡 4. Boilerplate check ---"
for f in LICENSE README.md .gitignore; do
  if [ -f "$f" ]; then
    echo -e "${GREEN}✅ $f exists${NC}"
  else
    echo -e "${YELLOW}⚠️  $f is missing${NC}"
    ISSUES=$((ISSUES + 1))
  fi
done
echo ""

# ── 5. Gitignore gaps ──
echo "--- 🟡 5. Gitignore coverage ---"
if [ -f .gitignore ]; then
  for pattern in '__pycache__' 'node_modules' 'dist' 'build' '.env' '*.local' '*.log' '*.db'; do
    if ! grep -q "$pattern" .gitignore 2>/dev/null; then
      echo -e "${YELLOW}⚠️  .gitignore missing: $pattern${NC}"
      ISSUES=$((ISSUES + 1))
    fi
  done
  echo -e "${GREEN}✅ .gitignore checked${NC}"
else
  echo -e "${RED}⚠️  No .gitignore at all${NC}"
  ISSUES=$((ISSUES + 1))
fi
echo ""

# ── Summary ──
echo "============================================"
echo "📊 AUDIT SUMMARY"
echo "============================================"
echo ""
if [ "$SECRET_LEAKS" -gt 0 ]; then
  echo -e "${RED}🔴 SECRET LEAKS: $SECRET_LEAKS — DO NOT PUSH${NC}"
fi
if [ "$TRASH_TRACKED" -gt 0 ]; then
  echo -e "${RED}🔴 TRASH TRACKED: $TRASH_TRACKED files${NC}"
fi
echo -e "${YELLOW}🟡 OTHER ISSUES: $ISSUES${NC}"
echo ""

if [ "$SECRET_LEAKS" -eq 0 ] && [ "$TRASH_TRACKED" -eq 0 ] && [ "$ISSUES" -eq 0 ]; then
  echo -e "${GREEN}✅ All checks pass — safe to push${NC}"
  exit 0
else
  echo -e "${RED}⚠️  Fix 🔴 items before pushing. Review 🟡 items.${NC}"
  exit 1
fi
