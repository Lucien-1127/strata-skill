---
name: strata-memory-compression
description: claude-mem 記憶壓縮模式內化至 STRATA V13.0
version: 0.3.0
author: Hermes
metadata:
  hermes:
    tags: [STRATA, Memory, Compression, Progressive-Disclosure, Auto-Compress]
---

# STRATA 記憶壓縮引擎

將 claude-mem (86K⭐) 的持久化記憶壓縮架構內化至 STRATA V13.0 的四層運算系統。這不是安裝 claude-mem 本體，而是將其**設計模式** — 漸進式揭露、觀察壓縮、跨會話上下文注入、混合搜尋 — 編碼為 STRATA 系統的原生推理流程。支援**全自動** cronjob 驅動壓縮（每 2h）與**手動**即時摘要兩種模式。

適用對象：已部署 STRATA V13.0 的 Hermes Agent 實例。不涉及 Node.js/Bun 安裝。

參考腳本：`scripts/auto-compress.py` — 自動偵測新 session 並觸發壓縮的 watchdog 程式。

## 當使用

- "讓記憶跨會話存活"
- "把 claude-mem 的模式融入 STRATA 系統"
- "如何實現自動上下文偵測和壓縮？"
- "跨 session 的記憶要怎麼壓縮？"
- "STRATA 系統需要跨會話記憶"
- "設定自動壓縮排程"

## 互補技能：`strat-memory-policy`

本技能專注於**執行層**的壓縮排程與自動化。壓縮策略（哪些內容值得記、哪些該丟、壓縮密度、跨會話優先級）由 **`strat-memory-policy`** 定義。兩者分工如下：

| 面向 | strat-memory-policy（策略層） | strata-memory-compression（執行層） |
|:-----|:----------------------------|:----------------------------------|
| 職責 | 決定「該壓縮什麼」 | 執行「如何壓縮」 |
| 觸發 | 手動呼叫（"執行記憶壓縮"） | cronjob 自動排程（每 2h） |
| 產出 | 壓縮策略決策（保留/丟棄/摘要密度） | 結構化摘要 + memory 寫入 |
| 工具 | `memory` + `session_search` | `cronjob` + `scripts/auto-compress.py` |

使用時**先載入 policy 決定策略，再讓 compression 執行排程**。若 policy 未定義壓縮策略，compression 會使用預設值（所有 session 均壓縮、摘要密度中等）。

## 核心模式對應

```
claude-mem 模式              →  STRATA 層級
─────────────────────────────────────────
PostToolUse Hook (自動捕捉)   →  系統回顯與防護層 → 觀察記錄
Session Summarization         →  深度推理層     → 摘要壓縮
Progressive Disclosure        →  提問重構層     → 分層注入
Hybrid Search (FTS5+Vector)  →  提問重構層     → 語意聚焦
Context Injection             →  精準解答層     → 注入歷史知識
Deduplication (SHA256)        →  系統回顯與防護層 → 重複過濾
Auto-Compress Watchdog        →  全系統排程     → cronjob + 偵測腳本
```

## 前提

- Hermes Agent 已運作
- STRATA V13.0 已部署 (`strata-v13` skill)
- Hermes 內建記憶系統已啟用（預設啟用，無需外部 provider）
- Python 3 可用（用於 auto-compress.py 偵測腳本）
- `cronjob` 工具可用於自動排程

## 使用方式

透過 `terminal` + `memory` + `execute_code` + `cronjob` + `session_search` 工具執行以下程序。

## 程序

### 0. 部署自動壓縮引擎（一次性設定）

建立 cronjob，每 2 小時自動掃描新 session 並壓縮摘要：

```bash
# 步驟 1: 確認 auto-compress.py 腳本存在於 ~/.hermes/scripts/
ls ~/.hermes/scripts/auto-compress.py

# 步驟 2: 建立 cronjob（注意 provider 需使用 custom:<name> 格式）
cronjob(action="create",
    name="STRATA自動壓縮",
    schedule="every 2h",
    script="auto-compress.py",
    skills=["strata-memory-compression"],
    model={"provider": "custom:deepseek", "model": "deepseek-v4-flash"},
    enabled_toolsets=["memory", "file", "terminal"],
    prompt="""你是一個自動記憶壓縮引擎，內化了 claude-mem 的記憶壓縮模式到 STRATA 系統。

讀取上方 auto-compress.py 的偵測輸出。若 trigger: true，執行：
1. 對每個 uncompressed_ids 中的 session_id，用 session_search(session_id=...) 讀取全文
2. 提取結構化摘要（完成事項、關鍵發現、待辦）
3. 用 memory 工具儲存每條摘要到 memory

若 trigger: false，回覆 [SILENT] 抑制空通知。"""
)
```

建立後自動運行，每次執行時 `auto-compress.py` 會：
1. 讀取 `~/.hermes/state.db` 的 `sessions` 表（欄位：id, title, started_at, message_count, tool_call_count, input_tokens, output_tokens）
2. 查詢 `messages` 表統計每個 session 的實際訊息數
3. 比對 `compression_locks` 表過濾已壓縮 session（跳過 msg_count <= 3 的短 session）
4. 若偵測到未壓縮活動 → 輸出 JSON（含 `trigger`, `uncompressed_ids`, `sessions` 陣列）
5. 更新 `~/.hermes/cron/output/auto-compress-state.json` 記錄 last_check_epoch

**重要：無新活動時輸出 `trigger: false`，Agent 必須回覆 `[SILENT]`（不含其他內容）以抑制空通知。** 只有真的有新摘要時才產出報告。

### 1. 系統回顯與防護層 — 觀察記錄自動化

模仿 claude-mem 的 PostToolUse Hook，在每次工具調用後自動記錄結構化觀察：

```python
# 記錄觀察的標準格式（透過 execute_code）
observation = {
    "type": "discovery|bugfix|decision|refactor|design",
    "title": "簡短標題（<=60字）",
    "narrative": "發生了什麼 + 為什麼重要",
    "facts": ["具體事實1", "具體事實2"],
    "project": "當前專案名稱",
    "timestamp": datetime.now().isoformat()
}
```

透過 `memory` 工具儲存關鍵事實：

```bash
hermes memory add "發現: claude-mem 使用 SHA256 前16字元做30秒去重"
hermes memory add "決策: 採用漸進式揭露節省 token"
hermes memory add "設計: 3層 MCP 搜尋工作流"
```

### 2. 提問重構層 — 漸進式揭露

分三層注入上下文以節省 token：

```
第一層（精簡索引，~50-100 tokens）：
  用戶之前關於 X 的主題有 3 次討論，涉及 A、B、C。

第二層（時間軸上下文，~200-300 tokens）：
  A 的最後決策是採用 Y 方案，原因為 Z。
  B 仍在進行，上次進度在 N 階段。

第三層（完整細節，~500-1000 tokens）：
  以下是 A 面向的完整分析報告：...
```

透過 `session_search` 實現分層檢索：

```python
# 第一層：發現相關 session
session_search(query="專案名稱 OR 關鍵字", limit=3)

# 第二層：展開指定 session 的時間軸
session_search(session_id="xxx", around_message_id=123, window=5)

# 第三層：完整閱讀
session_search(session_id="xxx")
```

### 3. 深度推理層 — 跨會話摘要壓縮

每段工作結束時產出結構化摘要。手動模式（說「幫我總結」）或自動模式（cronjob 觸發）都會產出此格式：

```
## 會話摘要 — {日期}

### ✅ 完成事項
- 項目 1

### 🧠 學到的事
- 發現 1

### 📋 待辦／下一步
- 項目 1（參考線索：[session_id]）

### 📌 關鍵決策
- 決策 1（理由）
```

手動儲存：

```bash
memory add "摘要 2026-07-06: 完成 claude-mem 深度研究，決定內化其記憶壓縮模式至 STRATA"
memory add "待辦: 研究 ChromaDB 向量搜尋如何整合到提問重構層"
```

### 4. 自動排程維護

設定完程序 0 的 cronjob 後自動運行。基本維護命令：

```bash
# 查看狀態
cronjob(action="list")

# 手動觸發一次
cronjob(action="run", job_id="<ID from list>")

# 若需暫停
cronjob(action="pause", job_id="<ID>")

# 若需移除並重建
cronjob(action="remove", job_id="<ID>")

# 查看執行日誌
ls ~/.hermes/cron/output/<job_id>/
cat ~/.hermes/cron/output/<job_id>/<latest-run>.md
```

### 5. 混合搜尋 — FTS5 + 語義檢索

```
混合搜尋策略：
┌─ FTS5（session_search）─┐    ┌─ 語義標籤（memory）───┐
│ 精準關鍵字匹配            │    │ 主題分類 + 關係連結     │
│ 適用：已知關鍵詞           │ +  │ 適用：模糊回憶           │
│ "Docker networking"       │    │ "跨會話記憶相關"         │
└───────────────────────────┘    └─────────────────────────┘
```

### 6. 精準解答層 — 動態上下文注入

```python
result = session_search(query="當前議題關鍵詞", limit=3, sort="newest")
# memory auto-injected. Session history on demand.
```

## 快速參考

| STRATA 層級 | claude-mem 模式 | Hermes 工具 |
|------------|----------------|-------------|
| 系統回顯與防護層 | Observation capture | `memory` + `execute_code` |
| 提問重構層 | Progressive Disclosure | `session_search` |
| 深度推理層 | Session Summarization | `memory` |
| 精準解答層 | Context Injection | `memory` + `session_search` |
| 全系統排程 | Auto-Compress Watchdog | `cronjob` + `scripts/auto-compress.py` |
| 全系統 | Deduplication | `memory` 內建去重 |

## 陷阱

- **memory 有字數上限**：只存關鍵事實（發現、決策、待辦），完整對話靠 `session_search`。
- **session_search 不是實時**：當前對話的內容在 session 結束後才可索引。
- **Cronjob provider key 解析問題**：若 cronjob 報錯 "no API key was found" 或 "Provider X is set but no API key"，原因是 config.yaml 的 API key 被 Hermes redactor 截斷（顯示為 `sk-53c...9aaf` 或 `«redacted:…»`）。解法雙管齊下：
  (a) 建立 cronjob 時必須明確指定 `model={"provider": "custom:<name>", "model": "..."}` 指向 `custom_providers` 區段，而非依賴頂層 `model.provider`。
  (b) 設環境變數 `DEEPSEEK_API_KEY` 加至 `~/.bashrc` 與 `~/.profile`，繞過 config redactor。
- **不要混用 claude-mem 和本模式**：若安裝了 claude-mem 本體，它會用自己的 Hook 系統。本模式是給 Hermes Agent 的獨立通道。
- **auto-compress.py 依賴 state.db schema**：Hermes 更新後若 schema 變動，腳本需同步更新。檢查 `cronjob(action="list")` 錯誤日誌。
- **cronjob 回覆約定**：無新活動時必須輸出 `[SILENT]`（精確匹配，無其他內容），否則 cron 引擎會發送空通知。有壓縮結果時才輸出正常報告。

## 驗證

```bash
# cronjob 狀態
cronjob(action="list")

# memory 中是否有摘要
hermes memory list | grep -i "摘要\|claude-mem\|STRATA"

# session_search 是否可檢索
session_search(query="claude-mem 記憶壓縮", limit=1)

# auto-compress 狀態檔
cat ~/.hermes/cron/output/auto-compress-state.json
```
