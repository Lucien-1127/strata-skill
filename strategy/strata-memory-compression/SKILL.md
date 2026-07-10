---
name: strata-memory-compression
description: claude-mem 記憶壓縮模式內化至 STRATA V13.0
version: 0.3.1
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

## 互補技能

| 技能 | 職責 |
|:----|:------|
| `strat-memory-policy` | 壓縮策略層 — 決定「該壓縮什麼」、內容分級（🔴🟡🟢） |
| `local-embedder-mem0-setup` | Mem0 OSS 安裝（Linux/Windows 雙平台） |
| `zhiyan-search` | ChromaDB + bge-m3 針對 zhiyan-legal docs/ 的向量搜尋 |

### STRATA → Mem0 向量橋接管線（參考：`references/mem0-bridge.md`）

將 STRATA 壓縮後的摘要**自動寫入** Mem0 向量庫，實現全自動 RAG 召回。2026-07-07 已將此步驟加入 cron prompt，每 2h 壓縮時自動同步：

```
對話 Session
    │
    ▼
STRATA cron (每 2h) ──→ MEMORY.md（純文字備份）
    │
    ├── save_summary_to_mem0.py ──→ Mem0.add() ──→ Qdrant 向量庫  ← 雙寫
    │                                                          │
    ▼                                                          ▼
新 session 開始                                       Mem0 自動注入 top-5
                                                    (~75-150 tokens/條)
```

**2026-07-07 更新**：cron prompt 已新增 Step 3（Mem0 同步），壓縮流程從「寫 MEMORY.md → 鎖」改為「寫 MEMORY.md → **同步 Mem0** → 鎖」。同時回溯同步 7 條歷史摘要，累計 16 條。

橋接腳本：`/home/ysga1/zhiyan-search/save_summary_to_mem0.py`

```bash
# 手動同步（增量）
cd /home/ysga1/zhiyan-search && python3 save_summary_to_mem0.py

# 查看同步狀態
python3 save_summary_to_mem0.py --status

# 強制全部重同步
python3 save_summary_to_mem0.py --all
```

**橋接腳本位置**：`/home/ysga1/zhiyan-search/save_summary_to_mem0.py`
**支援的設定檔**：`~/.hermes/mem0.json`（LLM + Embedder + Vector Store 設定）

功能一覽：
- 讀取 `~/.hermes/memories/MEMORY.md` 的 `§` 分隔條目
- 智慧分類（profile / preference / summary / decision / discovery / other）
- 增量跳過已同步條目（SHA256 hash 比對）
- 支援 `--dry-run`、`--status`、`--all` 旗標
- 獨立狀態檔：`~/.hermes/cron/output/mem0-sync-state.json`

**Qdrant 檔案鎖陷阱**：
Qdrant local 模式使用獨佔檔案鎖（`~/.hermes/mem0_qdrant/.lock`）。Hermes gateway 24h 運行時持有此鎖，外部 Python 腳本無法連線。

解法：Docker Qdrant Server 模式，用 HTTP 取代本地鎖：
```bash
# 啟動 server
docker run -d --name qdrant \
  -p 6333:6333 \
  -v ~/.hermes/mem0_qdrant_server:/qdrant/storage \
  qdrant/qdrant:latest

# 改 mem0.json 中的 vector_store.config:
#   "url": "http://localhost:6333"   (取代 "path": "...")
#   "api_key": null                  (不需 file lock)
```

重新啟動 Hermes gateway 後生效。需在 gateway 外執行（SSH 或 at 排程）。

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

# 步驟 2: 確認 save_summary_to_mem0.py 橋接腳本存在
ls /home/ysga1/zhiyan-search/save_summary_to_mem0.py

# 步驟 3: 建立 cronjob（注意 provider 需使用 custom:<name> 格式）
cronjob(action="create",
    name="STRATA自動壓縮",
    schedule="every 2h",
    script="auto-compress.py",
    model={"provider": "custom:deepseek", "model": "deepseek-v4-flash"},
    enabled_toolsets=["terminal", "file"],
    prompt="""自動記憶壓縮任務。上方是 auto-compress.py 的輸出。

trigger: false → [SILENT]
trigger: true → 執行：

1. 讀取 session：對 uncompressed_ids 中的每個 id，用 terminal 查 DB：
   terminal(command="cd ~/.hermes && sqlite3 state.db \\"SELECT * FROM messages WHERE session_id='{id}' ORDER BY id LIMIT 200;\\"")

2. 寫入 MEMORY.md — terminal echo >> 直接追加（**必須單行**，分兩行 echo 會造成格式漂移）：
   terminal(command="echo '§ 摘要 {日期}: {完成事項} | {關鍵發現}' >> ~/.hermes/memories/MEMORY.md")

3. Mem0 同步 — 將新摘要寫入向量庫供語意檢索：
   terminal(command="cd /home/ysga1/zhiyan-search && python3 save_summary_to_mem0.py")

4. 寫入壓縮鎖（表有 4 欄：session_id, holder, acquired_at, expires_at）：
   terminal(command="cd ~/.hermes && sqlite3 state.db \\"INSERT OR REPLACE INTO compression_locks VALUES('{session_id}', 'auto-compress', {now_epoch}, {now_epoch + 7200});\\"")

5. 產出簡短報告。

可用工具只有 terminal + file。""""
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

- **Cron 工具限制**：cron 環境中 `memory()` 工具和 `session_search` 工具**不可用**。所有操作必須透過 `terminal` + `file` 工具完成：
  - 讀取 session：`sqlite3 state.db "SELECT * FROM messages WHERE session_id='{id}' LIMIT 200;"`
  - 寫入記憶：`echo '§' >> ~/.hermes/memories/MEMORY.md` + `echo '摘要...' >> ~/.hermes/memories/MEMORY.md`
  - 寫入鎖：`sqlite3 state.db "INSERT OR REPLACE INTO compression_locks VALUES('{session_id}', 'auto-compress', {now_epoch}, {now_epoch + 7200})"`（4 欄全填）
- **不要附加任何 skill 到 cron job**：`skills=[]`（空陣列）。附加技能只會讓 cron agent 讀到「用 memory 工具」等誤導性文字，而這些工具在 cron 中不可用。prompt 本身必須自足。

- **lock 管理**：壓縮鎖須用 `terminal(command="cd ~/.hermes && sqlite3 state.db ...")` 寫入 `compression_locks` 表。該表有 4 欄：`(session_id, holder, acquired_at, expires_at)`。完整範例：
  ```
  INSERT OR REPLACE INTO compression_locks VALUES('{session_id}', 'auto-compress', {now_epoch}, {now_epoch + 7200})
  ```
  實戰陷阱：只傳 2 個值（session_id + expire）會 failed，因為第 2、3 欄不可為 null。

- **MEMORY.md 格式漂移（2026-07-09 發現）**：舊版 cron prompt 用 `echo '§'` + `echo '摘要'` 分兩行寫入，產生 `§\ncontent\n` 多行格式，`memory()` 工具無法解析此格式（期望 `§ content\n` 單行格式），導致後續 `memory(action='add')` 報「won't round-trip」。**解法**：(a) cron prompt 已修正為單行 `echo '§ 摘要...'`；(b) 若 MEMORY.md 已漂移，用 `write_file` 重寫為乾淨單行格式——STRATA 條目在系統 prompt MEMORY 段中仍有注入，不會遺失。

## 驗證

```bash
# cronjob 狀態
cronjob(action="list")

# memory 中是否有摘要
grep "摘要" ~/.hermes/memories/MEMORY.md

# session_search 是否可檢索
session_search(query="claude-mem 記憶壓縮", limit=1)

# auto-compress 狀態檔
cat ~/.hermes/cron/output/auto-compress-state.json

# 最新執行日誌
ls -t ~/.hermes/cron/output/<job_id>/ | head -3
```
