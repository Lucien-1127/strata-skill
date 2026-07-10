# GitHub Repo Metadata Batch Update — Worked Example

Real session: updating 9 repos under `Lucien-1127` with descriptions and topics. This file captures the specific blocker, the inventory data, and the intended commands.

## Repo Inventory (Before)

| Repo | Current Description | Current Topics | Action |
|------|-------------------|----------------|--------|
| CineAgent | `None` | `[]` | Update |
| hermes-skills | `None` | `[]` | Update |
| strata-skill | `None` | `[]` | Update |
| lucian-station | `None` | `[]` | Update |
| hermes-lucian | `None` | `[]` | Update |
| thai-zh-pwa | `None` | `[]` | Update |
| zhiyan-mvp | `智研 AI 法律系統 — 台灣法律 AI 研究助手 (PWA 前端 + FastAPI 後端)` | `[]` | Update |
| zhiyan-legal | `A reproducible research study of citation-grounding...` | `[8 topics]` | **Skip — already complete** |
| Lucien-1127 (profile repo) | `智研AI — 從 AI 法律研究到 AI 法律作業系統` | `[]` | Update topics only |

## Blocker Encountered

- ✅ SSH key (`~/.ssh/id_ed25519_github`) authenticates for `git push/pull` 
- ❌ Does NOT authenticate for GitHub API write operations (topics, description)
- ❌ No `GH_TOKEN`, `GITHUB_TOKEN`, or `GH_PAT` in environment, `.env` files, or credential stores
- ❌ `gh` CLI installed via binary download (`/tmp/gh`) but unauthenticated
- ❌ Device flow (`gh auth login`) requires opening a web browser — not possible in non-interactive session

**Root cause**: GitHub API metadata write operations require a PAT. SSH key is insufficient even though it works for git operations.

## Intended Commands (for when token is available)

```bash
export GH_TOKEN="<github_pat>"
/tmp/gh repo edit Lucien-1127/CineAgent \
  --description "AI 動畫影片自動化管線 — Agnes AI + Frame Chaining + 角色一致性" \
  --add-topic ai-video --add-topic animation --add-topic pipeline --add-topic agnes-ai

/tmp/gh repo edit Lucien-1127/hermes-skills \
  --description "Hermes Agent 技能庫 — 提示詞工程、自動化、DevOps、法律 AI" \
  --add-topic hermes-agent --add-topic skills --add-topic prompt-engineering

/tmp/gh repo edit Lucien-1127/strata-skill \
  --description "Hermes Agent 完整技能庫 — 139 項技能，FEG 架構，iron-laws 鐵律" \
  --add-topic hermes-agent --add-topic skills --add-topic prompt-engineering --add-topic ai-tools

/tmp/gh repo edit Lucien-1127/lucian-station \
  --description "AI 創意工具集合" \
  --add-topic creative --add-topic ai-tools

/tmp/gh repo edit Lucien-1127/hermes-lucian \
  --description "Dashboard 與管理介面" \
  --add-topic web --add-topic dashboard

/tmp/gh repo edit Lucien-1127/thai-zh-pwa \
  --description "泰中雙語 PWA 應用 — 語言學習與翻譯工具" \
  --add-topic pwa --add-topic thai-language --add-topic translation --add-topic bilingual

/tmp/gh repo edit Lucien-1127/zhiyan-mvp \
  --description "智研 AI 法律系統 — 台灣法律 AI 研究助手（PWA + FastAPI）" \
  --add-topic legal-tech --add-topic ai-law --add-topic pwa --add-topic fastapi --add-topic taiwan

# SKIP: zhiyan-legal (already complete with 8 topics)

/tmp/gh repo edit Lucien-1127/Lucien-1127 \
  --add-topic ai --add-topic legal-tech --add-topic taiwan \
  --add-topic hermes-agent --add-topic prompt-engineering
```

## Auth Diagnostic Commands Used

```bash
# Check SSH key
ssh -T git@github.com -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=accept-new

# Install gh without root
cd /tmp
curl -sL "https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz" -o gh.tar.gz
tar xzf gh.tar.gz
cp gh_2.67.0_linux_amd64/bin/gh /tmp/gh

# Test API write (expect 401)
curl -s -o /dev/null -w "%{http_code}" -X PATCH \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/Lucien-1127/CineAgent" \
  -d '{"description":"test"}'
# → 401 Unauthorized

# Check env vars
echo "${GH_TOKEN:+set}" ; echo "${GITHUB_TOKEN:+set}"
```
