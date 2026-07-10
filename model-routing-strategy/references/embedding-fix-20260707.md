# Embedding 路由修復記錄（2026-07-07）

## 問題

Mem0 和 ChromaDB 的 embedding 全部走 GitHub 免費路由的 `text-embedding-3-small`，三天內 919 次 429 錯誤（82% 失敗率），語意搜尋完全癱瘓。

## 診斷

```sql
-- FreeLLM DB 確認 embedding_models 路由
SELECT id, family, platform, model_id, dimensions, priority, quota_label
FROM embedding_models ORDER BY priority, id;

-- 確認預設 family
SELECT key, value FROM settings WHERE key='embeddings_default_family';
```

## 兩條管線解法

### Mem0（對話記憶）

改寫 `~/.hermes/mem0.json` 的 embedder config，直連 OpenRouter：

```json
{
  "model": "text-embedding-3-small",
  "openai_base_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-or-v1-...",
  "embedding_dims": 1536
}
```

優點：1536 維度不變，Qdrant 舊記憶相容。成本極低（$0.02/1M tokens）。

### zhiyan-search（文件索引）

改寫 `~/zhiyan-search/config.yaml`：

| 欄位 | 舊值 | 新值 |
|:-----|:-----|:-----|
| `api_base` | `http://localhost:8008/v1` | `https://openrouter.ai/api/v1` |
| `api_key` | `freely-local` | OpenRouter API key |
| `embedding_model` | `BAAI/bge-m3` | `text-embedding-3-small` |

### FreeLLM API（通用路由）

調整 `embedding_models` 表優先級：

| 優先級 | 模型 | 平台 | 維度 |
|:------:|:-----|:-----|:----:|
| 1 | NVIDIA Nemotron Embed VL | nvidia | 2048 |
| 5 | Google Gemini Embedding | google | 3072 |
| 100 | text-embedding-3-small (429) | github | 1536 |

並將 `embeddings_default_family` 改為 `llama-nemotron-embed-vl-1b-v2`。

## 教訓

1. GitHub 免費路由的 `text-embedding-3-small` 不穩定，有頻繁 429 限流
2. 換 embedding 模型要注意維度：1536≠2048≠1024，會使既有向量索引無法使用
3. OpenRouter 的 `/v1/embeddings` 端點完全 OpenAI 相容，是穩定的免費替代方案
