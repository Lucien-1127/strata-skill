# STRATA → Mem0 向量橋接

## 架構

```
STRATA cron (2h) → MEMORY.md → save_summary_to_mem0.py → Mem0 → Qdrant Server
```

## 前提

- Mem0 OSS v2.0.11+（`pip install mem0ai qdrant-client`）
- Qdrant Docker Server（`docker run -d --name qdrant -p 6333:6333 qdrant/qdrant`）
- FreeLLM API (:3001) 或任何 OpenAI-compatible endpoint，支援 chat + embedding
- dummy OPENAI_API_KEY 環境變數（繞過 OpenAI client key 格式檢查）

## 設定

### mem0.json（`~/.hermes/mem0.json`）

```json
{
  "mode": "oss",
  "user_id": "太陽",
  "agent_id": "hermes",
  "oss": {
    "llm": {
      "provider": "openai",
      "config": {
        "model": "auto",
        "openai_base_url": "http://localhost:3001/v1",
        "api_key": "freellmapi-..."
      }
    },
    "embedder": {
      "provider": "openai",
      "config": {
        "model": "text-embedding-3-small",
        "openai_base_url": "http://localhost:3001/v1",
        "api_key": "freellmapi-...",
        "embedding_dims": 1536
      }
    },
    "vector_store": {
      "provider": "qdrant",
      "config": {
        "collection_name": "mem0",
        "embedding_model_dims": 1536,
        "url": "http://localhost:6333",
        "api_key": null
      }
    }
  }
}
```

## Mem0 v2 API 重點

| 舊版 (v1.x) | v2.0+ | 說明 |
|:-----------|:------|:------|
| `m.search(query, user_id='X')` | `m.search(query, filters={'user_id': 'X'})` | filters dict |
| `m.get_all(user_id='X')` | `m.get_all(filters={'user_id': 'X'})` | filters dict |
| `m.add(content, user_id='X')` | `m.add(messages=[...], user_id='X', metadata={...})` | messages list, 非純文字 |
| `Memory(config_dict)` | `Memory.from_config(config_dict)` | factory method |

## 橋接腳本常用命令

```bash
# 只預覽不同步
OPENAI_API_KEY=sk-dummy python3 save_summary_to_mem0.py --dry-run

# 顯示同步狀態
OPENAI_API_KEY=sk-dummy python3 save_summary_to_mem0.py --status

# 執行同步
OPENAI_API_KEY=sk-dummy python3 save_summary_to_mem0.py

# 強制全部重新同步
OPENAI_API_KEY=sk-dummy python3 save_summary_to_mem0.py --all
```

## Qdrant 鎖衝突解決

Qdrant local 模式用獨佔檔案鎖。Hermes gateway 24h 持有此鎖時，外部腳本無法存取。

解法：切換為 Qdrant Server 模式（HTTP API）：
1. 用新目錄啟動 Docker Qdrant：`docker run -d -p 6333:6333 -v ~/.hermes/mem0_qdrant_server:/qdrant/storage qdrant/qdrant`
2. 改 mem0.json 用 `url` 取代 `path`
3. 重啟 Hermes gateway
4. 用 bridge script 重新同步所有摘要（--all）

## FreeLLM API 注意點

- `auto` 模型自動路由至可用 provider
- 部分模型（deepseek-v4-flash, glm-4.7-flash）容易觸發 rate limit（429）
- 若持續 429，改用 `auto` 或 `kimi-k2.6`
- Embedding 用 `text-embedding-3-small`（1536 dim），走 GitHub 免費 provider
