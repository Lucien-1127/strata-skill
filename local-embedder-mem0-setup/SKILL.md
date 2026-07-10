---
name: local-embedder-mem0-setup
description: Install and configure Mem0 OSS with Qdrant vector store.
version: 0.2.0
author: Hermes
metadata:
  hermes:
    tags: [Memory, Mem0, Qdrant, Embedding]
---

# 本機 Embeddings + Mem0 OSS 記憶架構

## 架構

```
├─ LLM:       DeepSeek API (sk-7ba...f7cc)
├─ Embedder:  本機 all-MiniLM-L6-v2 → localhost:8765/v1/embeddings
├─ Vector:    Qdrant 本地檔案 (~/.hermes/mem0_qdrant)
└─ Provider:  Mem0 OSS (hermes plugin)
```

## 啟動 Embeddings 伺服器

```bash
cd /c/Users/ysga1/local-embedder
python server.py
```

或執行 `start-embedder.bat`。

## 配置檔案

**`~/.hermes/mem0.json`:**

```json
{
  "mode": "oss",
  "user_id": "sun",
  "agent_id": "hermes",
  "oss": {
    "llm": {
      "provider": "openai",
      "config": { "model": "deepseek-v4-flash" }
    },
    "embedder": {
      "provider": "openai",
      "config": {
        "model": "local-embedder",
        "openai_base_url": "http://127.0.0.1:8765/v1",
        "api_key": "sk-dummy-local",
        "embedding_dims": 384
      }
    },
    "vector_store": {
      "provider": "qdrant",
      "config": { "path": "C:/Users/ysga1/.hermes/mem0_qdrant" }
    }
  }
}
```

**`~/.hermes/.env`:** 需有 `OPENAI_API_KEY` (DeepSeek key)

**config.yaml:** `memory.provider: mem0`

## 啟用條件

1. Embeddings 伺服器必須在背景執行（localhost:8765），或使用 FreeLLM API
2. `.env` 有 OPENAI_API_KEY（DeepSeek 方案）或 FreeLLM API key
3. Qdrant 路徑存在（自動建立）

## 替代方案：FreeLLM API 作 Embedder

若已有 FreeLLM API Docker（本機 `:3001`），可直接取代自架 embedder，同一容器同時服務 LLM + embedding：

```json
"embedder": {
  "provider": "openai",
  "config": {
    "model": "text-embedding-3-small",
    "openai_base_url": "http://localhost:3001/v1",
    "api_key": "<FreeLLM API Key>",
    "embedding_dims": 1536
  }
}
```

**優點**：FreeLLM API 內建 `/v1/embeddings` 路由至免費 provider（GitHub 等），不需本機下載模型、不需額外 server 行程。

### 替代方案 B：OpenRouter Embedding（2026-07-07 實測）

當 FreeLLM 的 GitHub embedding 路由被 429 限流時，Mem0 的 embedder 可直接改走 OpenRouter：

```json
"embedder": {
  "provider": "openai",
  "config": {
    "model": "text-embedding-3-small",
    "openai_base_url": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "embedding_dims": 1536
  }
}
```

**優點**：保留 1536 維度（Qdrant 舊資料相容），成本極低（$0.02/1M tokens），$5 可用約 2300 萬次。
**金鑰格式**：OpenRouter API key 以 `sk-or-v1-` 開頭。
**金鑰儲存**：`~/.hermes/env/openrouter.env`，`chmod 600`。

### 替代方案 C：NVIDIA Nemotron Embedding（免費 2048 維）

透過 FreeLLM API 可使用 NVIDIA 免費 embedding：

```json
"embedder": {
  "provider": "openai",
  "config": {
    "model": "nvidia/llama-nemotron-embed-vl-1b-v2",
    "openai_base_url": "http://localhost:3001/v1",
    "api_key": "<FreeLLM API Key>",
    "embedding_dims": 2048
  }
}
```

**注意**：2048 維 ≠ 1536 維，若 Qdrant 已存 1536 維向量，需重建 collection。

**模型選擇**：實測 `text-embedding-3-small` (1536 dim) 和 `text-embedding-3-large` 均可路由。若 embedding 被限流（429），切換至不同 model name 或 provider 通常可繞過。

### 維度相容性速查表

| Embedding 方案 | 維度 | Qdrant 相容 | 成本 |
|:---------------|:----:|:-----------:|:----:|
| OpenRouter text-embedding-3-small | 1536 | ✅ 可沿用 | $0.02/1M |
| FreeLLM NVIDIA Nemotron | 2048 | ❌ 需重建 | 免費 |
| FreeLLM GitHub text-embedding-3-small | 1536 | ✅ 但常 429 | 免費 |
| 自架 all-MiniLM-L6-v2 | 384 | ❌ 需重建 | 免費 |

## 注意事項

- 384 dims (all-MiniLM-L6-v2) — 不是 OpenAI 的 1536；FreeLLM `text-embedding-3-small` 是 1536
- msvcrt import warning 是 Qdrant 在 Windows 上的已知問題，不影響功能
- 新 Hermes session 會自動載入 mem0（記憶寫入 + 預取）
- FreeLLM API key 通常存在 `~/.hermes/env/freellmapi.env` 或 `~/.hermes/config.yaml` 的 `custom_providers` 區塊

### ChromaDB 1.5.9 批量寫入陷阱

ChromaDB PersistentClient 在逐檔 `collection.add()` 時可能觸發 Rust 內部鎖定（`readonly database` / `no such table: max_seq_id`）。**解法**：收集所有 chunks 後一次性寫入：

```python
# ❌ 逐檔寫入（觸發鎖定）
for filepath in files:
    collection.add(embeddings=..., ids=...)

# ✅ 一次全部寫入（繞過鎖定）
all_emb, all_ids, all_meta = [], [], []
for filepath in files:
    all_emb.extend(file_emb)
    all_ids.extend(file_ids)
    all_meta.extend(file_meta)
collection.add(embeddings=all_emb, ids=all_ids, metadatas=all_meta)
```

### Linux vs Windows 路徑對照

| 項目 | Linux (GCP VM) | Windows (本機) |
|:----|:-------------|:--------------|
| Qdrant 路徑 | `/home/user/.hermes/mem0_qdrant` | `C:/Users/user/.hermes/mem0_qdrant` |
| FreeLLM API | Docker `:3001` | 另裝或自架 |
| 本地 embedder | `localhost:8765` | `localhost:8765` |
| 金鑰檔案 | `~/.hermes/env/freellmapi.env` | `%USERPROFILE%\\.hermes\\.env` |

### Qdrant 檔案鎖（多 process 不可共存）

Qdrant local 模式使用**獨佔檔案鎖**（`~/.hermes/mem0_qdrant/.lock`）。Hermes gateway 24h 運行時持有此鎖，外部 Python 腳本無法同時連線。

**固定解法：Qdrant Docker Server**
```bash
# 1. 啟動 Qdrant Server（新目錄，不搶舊鎖）
docker run -d --name qdrant \
  -p 6333:6333 \
  -v ~/.hermes/mem0_qdrant_server:/qdrant/storage \
  qdrant/qdrant:latest

# 2. 改 mem0.json — 用 url 取代 path
#    修改 vector_store.config:
#    "url": "http://localhost:6333"
#    "api_key": null

# 3. 重啟 Hermes gateway（需在 gateway 外執行）
systemctl --user restart hermes-gateway
```

### dummy OPENAI_API_KEY（FreeLLM 方案必須）

使用 FreeLLM API 作 embedder 時，OpenAI Python client v2.x 會**驗證 api_key 格式**（必須 `sk-` 開頭）。FreeLLM key (`freellmapi-...`) 會被拒絕。**必須在 `~/.hermes/.env` 設 dummy key：**
```
OPENAI_API_KEY=sk-placeholder-for-mem0
```
不影響實際呼叫 — embedding 仍走 FreeLLM 的 `openai_base_url`。

### Mem0 LLM 路由坑：FreeLLM 429 限流（2026-07-09 實戰修復）

Mem0 的 `oss.llm` 和 `oss.embedder` 是兩層獨立路由，**分開設定，坑也分開**。

| 層級 | 走 FreeLLM (:3001) | 建議 |
|------|:------------------:|:----:|
| **Embedder** | ✅ 可行（量小、免費） | 可走 FreeLLM |
| **LLM** | ❌ 必炸 429 | 直連 DeepSeek API |

**症狀：** STRATA 壓縮 cron 觸發 Mem0 同步時，log 噴大量：
```
ERROR mem0.memory.main: LLM extraction failed: Error code: 429
{'error': {'message': 'All models exhausted: 2 routes checked (2 rate-limited or on cooldown)..'}}
```

**根因：** `mem0.json` 中 `oss.llm.config.openai_base_url` 設為 `http://localhost:3001/v1`（FreeLLM）。Mem0 發送 LLM extraction 請求到 FreeLLM，FreeLLM 的 `auto` 路由檢查上游多條 provider 配額，當所有上游都被 rate limit 時回傳 429。

**解法：LLM 直連 DeepSeek API，不走 FreeLLM。Embedder 可以繼續走 FreeLLM。**

```json
{
  "oss": {
    "llm": {
      "provider": "openai",
      "config": {
        "model": "deepseek-v4-flash",
        "openai_base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    },
    "embedder": {
      "provider": "openai",
      "config": {
        "model": "text-embedding-3-small",
        "openai_base_url": "http://localhost:3001/v1",
        "api_key": "<FreeLLM API Key>",
        "embedding_dims": 1536
      }
    }
  }
}
```

**LLM 和 Embedder 可以指向不同的 base_url**，甚至可以使用不同 provider。

### Hermes Fallback Model（provider 層級備援）

當主要 provider 被 rate limit 時，Hermes 支援自動 failover 到備援 provider：

```yaml
# ~/.hermes/config.yaml 添加：
fallback_model:
  provider: openrouter
  model: deepseek/deepseek-v4-flash
```

需設定 `OPENROUTER_API_KEY` 環境變數（或寫入 `~/.hermes/.env`），重啟 Gateway 生效。
Failover 在 429 / 529 / 503 / 連線失敗時自動觸發。

### Mem0 v2.x API 變更

v2.0+ 改用 `filters` 參數：
```python
# ✅ v2.0+
m.search(query="...", filters={"user_id": "太陽"})
m.get_all(filters={"user_id": "太陽"})

# ❌ v1.x（v2 報錯）
m.search(query="...", user_id="太陽")
```

### STRATA → Mem0 橋接

詳細的橋接管線設計與 `save_summary_to_mem0.py` 腳本說明見 `strata-memory-compression` 技能下的 `references/mem0-bridge.md`。

## 故障排除

```bash
# 測試 embedder
curl -s http://127.0.0.1:8765/health

# 測試 embeddings
curl -s http://127.0.0.1:8765/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input":"test"}'

# 重設向量庫
rm -rf ~/.hermes/mem0_qdrant
```
