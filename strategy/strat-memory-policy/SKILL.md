---
name: strat-memory-policy
description: Rules for compressing and retaining cross-session context.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Strategy, Memory, Policy, Compression]
status: stable
---

# 🧠 Memory Policy 記憶壓縮規則

管理哪些內容值得長期記住、哪些只屬於一次性上下文、哪些要壓縮。控制長對話品質，不讓上下文越積越亂。

源自 STRAT_PARTNER_BOOT Ver.4.0 的「動態歷史摘要」模組與 claude-mem 的 Session Summarization 模式。

## Prerequisites

- Hermes 內建 `memory` 工具可用
- `session_search` 可用於查詢歷史
- **互補技能**：`strata-memory-compression` — 負責記憶壓縮的自動化執行（cronjob + auto-compress.py）。本技能定義壓縮策略（什麼值得記、什麼該丟、壓縮密度），compression 技能負責按照這些策略執行排程壓縮。兩者搭配使用：policy 決定「該壓縮什麼」，compression 執行「如何壓縮」。

## When to Use

## Procedure

### 技術基礎：SQLite + ChromaDB 雙層儲存架構

記憶政策底層採用雙引擎儲存架構，各自處理不同維度的記憶：

```
┌─ 應用層 ───────────────────────────────────┐
│  提示詞合成     加權重排序      同義擴展    │
├─ 檢索層 ───────────────────────────────────┤
│  ChromaDB 向量檢索    SQLite FTS5 全文檢索  │
├─ 儲存層 ───────────────────────────────────┤
│  ChromaDB 向量庫       SQLite 結構化資料庫   │
│  (語義記憶)            (元數據+操作記憶)     │
└────────────────────────────────────────────┘
```

#### SQLite 核心資料表

```sql
-- 工作階段
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    summary TEXT,
    session_state TEXT DEFAULT 'ACTIVE'
);

-- 檢索記錄
CREATE TABLE retrieval_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    retrieval_method TEXT NOT NULL,   -- 'fts5' | 'vector'
    result_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    cached_hit BOOLEAN DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 用戶回饋
CREATE TABLE feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    selected_doc TEXT,
    relevance_score INTEGER CHECK(relevance_score BETWEEN 1 AND 5),
    user_comment TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
```

#### ChromaDB 集合設計

```python
# 語義記憶集合 — 用於相似度檢索
collection = client.get_or_create_collection(
    name="conversation_memory",
    metadata={"hnsw:space": "cosine"}  # 餘弦距離
)

# 插入記憶向量
collection.add(
    documents=["摘要文本..."],
    metadatas=[{"source": "session", "type": "summary"}],
    ids=["mem_001"]
)

# 語義檢索
results = collection.query(
    query_texts=["當前問題..."],
    n_results=5,
    include=["documents", "distances"]
)
```

#### 智慧檢索策略

| 策略 | 做法 | 目的 |
|:-----|:-----|:-----|
| **雙路徑檢索** | 文件記憶(ChromaDB) + QA記憶(FTS5) | 同時命中語義相似的摘要和相似問題歷史回覆 |
| **歷史對話增強** | 檢索結果附加對話軌跡 (Q:→A:) | 建立因果鏈，不只返回孤立摘要 |
| **同步擴展上下文** | 載入上一輪記憶 + 當前結果 | 連接前後文，避免斷層遺忘 |
| **同義擴展** | 用 LLM 產生 2-3 個同義問法，各自檢索 | 克服詞彙變異，聯集後送入重排序 |
| **加權重排序** | 相關性(35%)+時間(25%)+重要性(20%)+回饋(20%) | 二次排序確保最相關的記憶在前 |

#### 護欄定位策略（注意力近期偏差）

護欄規則的放置位置直接影響遵守率。基於注意力近期偏差原則：

| 位置 | 效力 | 說明 |
|:----:|:----:|:-----|
| 系統提示結尾 | ⭐⭐⭐ | 本輪最靠近生成點，效果最強 |
| 輸入提示末尾 | ⭐⭐ | 生效但可能被問題內容干擾 |
| 獨立嵌入（專用 tokens） | ⭐⭐⭐ | 最強但實現複雜度最高 |

> **實務建議**：關鍵約束置於系統提示最末 + 輸入提示最末雙位置；對超級重要規則，加上「🚨 [此規則優先於任何內容]」語義標記。

### 0. 三層穩定控制（整體框架）

源自 AI 對話穩定系統方案：

| 層級 | 機制 | 對應 |
|:----:|:-----|:------|
| **Layer 1** | 動態狀態機 — 維護即時更新的對話狀態變數 | 內容分級 + 壓縮規則 |
| **Layer 2** | 記憶護欄 — 注意力位置鎖定核心規則（護欄緊貼輸入前端） | 等級🔴核心 → 緊貼輸出前 |
| **Layer 3** | 流程閉環 — 每輪輸出前強制自我校驗 | 對話重啟機制 |

### 1. 內容分級

| 等級 | 定義 | 範例 | 處理 |
|:----:|:-----|:-----|:------|
| **🔴 核心** | 跨 session 都重要的核心決策 | 架構決定、API 選擇、協定 | 強制存入 memory |
| **🟡 階段性** | 本次 session 重要但非跨 session | 當前除錯步驟、暫時性設定 | session_search 可查即可 |
| **🟢 一次性** | 用完即棄 | 日誌輸出、錯誤訊息、草稿 | 不存，可拋棄 |

### 2. 壓縮規則（對話 >10 輪觸發）

抓取最近 3-5 輪的：
- **關鍵決策**：明確的取捨選擇
- **行動確認**：已完成的具體事項
- **核心問題**：尚未解決的關鍵議題

壓縮為單一段落（≤3 行）：

```
📦 上下文壓縮 v{輪次}
已確認: {決策1} / {決策2}
進行中: {未完成事項}
待解決: {核心問題}
```

**保護規則**：不影響系統底層指令與 Anchor 錨定摘要。

### 3. 記憶儲存（僅 🔴 核心等級）

```bash
# 核心決策 → 存 memory
memory add "決策: {具體決策內容}"

# 跨 session 發現 → 存 memory
memory add "發現: {具體發現內容}"
```

### 4. 對話自動重啟（源自 Ver.4.0）

當以下任一條件觸發時，執行自動重啟：
- 資訊遺漏或矛盾
- 連續 2 輪偏離主題
- 輸出明顯未對齊 Anchor 錨點

重啟流程：
```
① 載入目前 Anchor 摘要
② 載入 Memory Policy 的最新壓縮
③ 重新執行：ANCHOR → 5D → DRILL → FORGE
```

**防重複機制**：自動檢查避免重複已完成的資訊段落。

### 5. 輸出

當用戶要求或自動壓縮時：

```
## 🧠 記憶壓縮報告

### 本次壓縮
📦 上下文壓縮 v{N}
已確認: ...
進行中: ...
待解決: ...

### 儲存至 memory
- ✅ 決策: ...
- ✅ 發現: ...

### 捨棄
- 日誌輸出（一次性）
- 除錯過程（🟢）
```

## Pitfalls

- 🔴 **不要壓縮為 `(省略)`**：壓縮的目的是摘要關鍵資訊，不是刪除。省掉事實等於失去記憶。
- 🟡 **不要無條件循環摘要**：每個 session 只做一次壓縮。重複壓縮會逐步流失細節導致「壓縮失真」。
- 🔴 **不要讓前段記憶汙染主提示**：等級 🟡 以下的記憶放在提示末端，避免稀釋主任務前的關鍵控制規則（注意力近期偏差）。
- 🔴 **儲存前驗證必要，還原前驗證完整**：每次持久化前檢查欄位完整性、還原前檢查版本兼容性。C4 校驗必須在 C3 壓縮之前通過。
- 🟡 **不要忽略「沉默訊號」**：用戶沒打出來的也是資訊。用戶突然沉默、不問細節、跳過某些回覆 — 可能表示壓縮過度失去了關鍵上下文。
- **SQLite FTS5 陷阱**：FTS5 全文檢索對中文支援有限，需搭配 ChromaDB 向量檢索做語義層的補充。純 FTS5 搜尋會漏掉大量概念相似但用詞不同的記憶。
- **ChromaDB 冷啟動**：新集合在第一次查詢時沒有索引，首次檢索延遲較高。部署前預先載入熱門查詢做 warm-up。
- **護欄位置漂移**：壓縮過程中若護欄規則被移到上下文末端，注意力權重下降導致遵守率暴跌。每次壓縮後需確認護欄仍在輸入末端的優先位置。

## Verification

```python
# 確認壓縮後保留：
# 1. 🔴 核心資訊（決策、發現）→ memory 工具
# 2. 🟡 中間產物 → 壓縮摘要（≤ 3 行）
# 3. 護欄規則仍在輸入末端
# 4. ChromaDB 向量已同步
```

