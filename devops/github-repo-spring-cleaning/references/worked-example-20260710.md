# GitHub Repo Spring-Cleaning — 2026-07-10 實戰記錄

> 一次性整理 10 個公開 repo：補 LICENSE/README/.gitignore、修 git email、安全掃描、更新 topics、git history 垃圾清除。

## 啟動清單

1. 掃描 GitHub 帳號：`api.github.com/users/Lucien-1127/repos` → 10 個 repo
2. 掃描本機所有 git repo：`find ~ -name '.git' -maxdepth 4` → 列出 remote/branch/dirty 狀態
3. 檢查每個遠端 repo 的 contents：有無 README/LICENSE/.gitignore

## 發現

| 面向 | 初始狀態 | 修復後 |
|------|---------|--------|
| Git email | 3+ repo 用 `hermes@nousresearch.com` | 全部 `lucien127@proton.me` |
| LICENSE | 只有 1/10 有 (zhiyan-legal MIT) | 9/10 有 MIT (profile repo 不需要) |
| README | 8/10 有 | 10/10 有 |
| .gitignore | 7/10 有 | 9/10 有 |
| Topics | 全部空白 | 已設定（需 PAT） |
| Description | 多個「無說明」 | 已更新（需 PAT） |
| Git history 垃圾 | 67MB MP4 + 38MB index cache | filter-branch 清除 |
| Database in tracking | regulation_tracker.db | git rm --cached |

## 執行策略

子代理平行處理：

- 子代理 1：profile README 更新（bio/tech stack/contact）
- 子代理 2：strata-skill README + LICENSE
- 子代理 3：批量 LICENSE push（本機 + clone remote）
- 子代理 4：thai-zh-pwa 從零補三件套
- 子代理 5：topics/description 更新（需要 PAT）

## 關鍵陷阱（實戰驗證）

### 1. Git email 是 per-repo 設定
`git config --global user.email` 設對了，但每個 repo 的 `.git/config` 可以獨立覆蓋。
**教訓**：一定要 `cd <repo> && git config user.email`（不加 `--global`）。

### 2. SSH auth ≠ REST API auth
有 SSH key 可以 git push/pull，但 `api.github.com` 全拒絕。
無法用 SSH 做：設定 topics、更新 description、archive repo。

### 3. zhiyan-legal push 被拒
子代理加了 LICENSE，`git push` 被拒因為遠端已有新 commit。
**解法**：`git pull --rebase origin main && git push`

### 4. strata-skill git history 清單

被 filter-branch 清除的垃圾：

| 類別 | 路徑 | 大小 |
|------|------|------|
| MP4 影片 | `media-pipeline/scripts/output/*.mp4` | 67MB（18 個檔案） |
| Index cache | `.hub/index-cache/hermes-index.json` | 38MB |
| Hub logs/config | `.hub/*` | 數 KB |
| pycache | `legal/.../__pycache__/*.pyc` | 數 KB |

### 5. 垃圾檔案 QC 檢查命令

```bash
# 一鍵掃描所有垃圾檔案
cd <repo>
echo "=== .db ===" && git ls-files '*.db' '*.sqlite' '*.sqlite3' 2>/dev/null
echo "=== .log ===" && git ls-files '*.log' 2>/dev/null
echo "=== __pycache__ ===" && git ls-files -- '*/__pycache__/*' '*.pyc' 2>/dev/null
echo "=== .env ===" && git ls-files '.env*' 2>/dev/null
echo "=== Large >1MB ===" && git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && test "$(stat -c%s "{}")" -gt 1048576 && echo "{}"' 2>/dev/null
echo "=== node_modules ===" && git ls-files 'node_modules/' 2>/dev/null | wc -l
echo "=== dist/ build/ .next/ ===" && git ls-files 'dist/' 'build/' '.next/' 2>/dev/null | wc -l
```

### 6. filter-branch 後驗證歷史大小

```bash
# 最大 5 個歷史檔案
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | \
  sort --numeric-sort --key=2 | \
  tail -5 | \
  awk '{print $3, $2/1024/1024 " MB"}'
```

### 7. QC 第二階段發現（Phase 2 QA — 6 個高優先問題）

首次 QC 過關後，做深度二次掃描才發現的問題：

| # | 等級 | Repo | 問題 | 修復 |
|---|---|---|---|---|
| 1 | 🔴 | hermes-proxy-console | README 仍是 Vite 預設 | 改寫繁體中文完整說明 |
| 2 | 🔴 | hermes-skills | .gitignore 僅 3 行 | 補全 17 條排除（但 archived 無法 push） |
| 3 | 🔴 | Lucien-1127 | 完全無 .gitignore | 新建 5 條 |
| 4 | 🔴 | zhiyan-mvp | brand-site/ 含 21MB build artifacts | `git rm --cached` + .gitignore |
| 5 | 🔴 | hermes-skills | 參考文件含真實金鑰 | patch 為佔位符 |
| 6 | 🔴 | lucian-station | sync.log (41KB) + logs/ 被追蹤 | `git rm --cached` |

**教訓**：第一輪 QC（十個 repo 補 LICENSE/README）不夠。必須做第二輪深度掃描，包含：
- 每個 repo 的 `git ls-files` 垃圾檢查
- 歷史最大檔案檢查
- 敏感資料 regex 掃描

### 8. strata-skill git history 瘦身成果

清理前：pack 大小約 105MB（18 個 MP4 + 38MB index cache + pycache）
清理後：pack 大小 ≈ 0（無大型 binary）
過濾器套用順序：
1. `git rm --cached --ignore-unmatch .hub/index-cache/hermes-index.json`
2. `git rm --cached --ignore-unmatch 'media-pipeline/scripts/output/*.mp4' 'media-pipeline/scripts/output/*.txt' 'media-pipeline/scripts/output/*.json'`
3. `git rm --cached --ignore-unmatch '.hub/*'`
4. `git rm --cached --ignore-unmatch '*/__pycache__/*' '*.pyc'`

**注意**：每個 filter-branch 會改寫 commit hash，所以要按照依賴順序執行（先清最大檔案），減少交互影響。

## 最終 repo 狀態

| Repo | 狀態 | Topics | Description | LICENSE | README |
|---|---|---|---|---|---|
| Lucien-1127 | 🟢 active | 6 | ✅ | ⏭️ profile | ✅ |
| CineAgent | 🟢 active | 6 | ✅ | ✅ MIT | ✅ |
| hermes-skills | 🔴 archived | 4 | ✅ | ✅ MIT | ✅ |
| strata-skill | 🟢 active | 5 | ✅ | ✅ MIT | ✅ zh-TW |
| zhiyan-legal | 🟢 active | 8 (既有) | ✅ 不變 | ✅ MIT | ✅ |
| zhiyan-mvp | 🟢 active | 6 | ✅ | ✅ MIT | ✅ |
| hermes-lucian | 🔴 archived | 4 | ✅ | ✅ MIT | ✅ |
| lucian-station | 🔴 archived | 3 | ✅ | ✅ MIT | ✅ |
| thai-zh-pwa | 🟢 active | 4 | ✅ 從零補齊 | ✅ MIT | ✅ zh-TW |
| hermes-proxy-console | 🟢 new | 7 | ✅ | ✅ MIT | ✅ (33 files) |
