---
name: hermes-memory-setup
description: "評估、安裝、設定 Hermes Agent 的外部記憶 Provider（Honcho, Mem0, OpenViking, Hindsight 等 8 種）"
---
# hermes-memory-setup

## 📖 Description

評估、安裝、設定 Hermes Agent 的外部記憶 Provider（Honcho, Mem0, OpenViking, Hindsight 等 8 種）

**Tags**: hermes, memory, provider, mem0, openviking, qdrant, setup

---

# Hermes 外部記憶 Provider 安裝指南

## 適用時機
- 使用者要求啟用長期跨 Session 記憶
- 內建記憶（MEMORY.md / USER.md）不敷使用
- 需要自動提取事實、語意搜尋、知識圖譜

## 快速指令

```bash
hermes memory setup              # 互動選擇 + 設定
hermes memory status             # 查看當前啟用的 provider
hermes memory off                # 停用外部 provider
```

## Provider 一覽

| Provider | 費用 | 適合場景 | 需要 Server |
|----------|------|---------|------------|
| **Honcho** | 雲端收費 / 自架免費 | 多代理系統、跨 Session 用戶建模 | ✅ 需 API / 自架 |
| **Mem0** | 雲端收費 / OSS 免費 | 懶人自動提取事實、去重 | ❌ 本機模式免 server |
| **OpenViking** | 免費 (AGPL-3.0) | 自架知識庫、分層瀏覽 | ✅ 需 `openviking-server` |
| **Hindsight** | 免費 | 知識圖譜 + 跨記憶推理 | ✅ |
| **Holographic** | 免費 | 全像壓縮儲存 | ❌ |
| **RetainDB** | 免費 | 輕量嵌入式記憶庫 | ❌ |
| **ByteRover** | 免費 | 分散式記憶 | ✅ |
| **Supermemory** | 免費 | 超長期記憶 | ❌ |

## 選擇指引

### 免費 + 本機優先 → Mem0 OSS
```bash
pip install mem0ai chromadb qdrant-client
hermes memory setup mem0 --mode oss --oss-llm-key <key> --oss-vector qdrant
```

### 自架知識庫 → OpenViking
```bash
pip install openviking
openviking-server
hermes memory setup   # 選 openviking
```

### 最省事 → 維持內建記憶
- 已在運作，不需安裝
- 足夠容納 10-15 條事實
- Agent 會自動維護和壓縮

## 設定檔位置

| 檔案 | 用途 |
|------|------|
| `~/.hermes/config.yaml` → `memory.provider` | 啟用哪個 provider |
| `~/.hermes/<provider>.json` | Provider 專屬設定（如 `mem0.json`） |
| `~/.hermes/.env` | API keys（secret） |

## 已知陷阱

### `model.context_length` 蓋掉 provider 設定
Hermes 有兩層 context_length：
- **Model 層級**（`config.yaml → model.context_length`）— 全域蓋板
- **Provider 層級**（`custom_providers → models → context_length`）— 各 model 設定

後者即使設了 1M，如果前者只有 200K，**實際上只會用到 200K**。

**修正：**
```bash
hermes config set model.context_length 1000000
```

### DeepSeek 沒有 Embeddings API
在 Mem0 OSS 中，embedder 只能用 OpenAI（付費）或 Ollama（免費本機）。
使用 DeepSeek 當 embedder 會回 **404**。需搭配 Ollama nomic-embed-text 或 OpenAI。

### Mem0 LLM Extraction 429（FreeLLM 路由陷阱）

Mem0 的 LLM extraction（記憶事實提取）預設走 `openai_base_url` 設定的端點。如果 LLM extraction 指向 **FreeLLM**（`localhost:3001/v1`），當 FreeLLM 上游全被 rate limit 時 Mem0 會持續噴 429。

**解法：** `mem0.json` 中的 LLM extraction 要走**直接 upstream 端點**（如 `https://api.deepseek.com/v1`），不要經過 FreeLLM。embedder 仍可走 FreeLLM／OpenRouter，但 LLM extraction 必須直連。

詳見 `references/mem0-llm-routing-429-fix.md`。

### FreeLLM API 作 Embedder（推薦免費方案）
若已有 FreeLLM API（如 Docker 容器 `:3001`），可直接當作 Mem0 的 embedder，同一容器同時服務 LLM + embedding：

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

FreeLLM API 內建 `/v1/embeddings` 路由至免費 provider（GitHub 等），不需本機下載模型、不需額外 server。

#### 關鍵陷阱：dummy OPENAI_API_KEY 環境變數

OpenAI Python client v2.x 在初始化時會**驗證 api_key 格式**（必須是 `sk-...` 開頭）。FreeLLM 的 key 格式（如 `freellmapi-...`）會被拒絕。

**解法**：在 `~/.hermes/.env` 設一個 dummy OpenAI key：
```
OPENAI_API_KEY=sk-placeholder-for-mem0
```
此 key 僅用於通過 OpenAI client 的初始化檢查，實際 embedding 請求仍走 FreeLLM API 的 `openai_base_url`。

### Mem0 v2.x API 變更
Mem0 v2.0+ 改用 `filters` 參數取代舊版頂層實體參數：

```python
# ❌ v1.x（v2 不能用）
m.search(query="...", user_id="太陽")

# ✅ v2.0+
m.search(query="...", filters={"user_id": "太陽"})
m.get_all(filters={"user_id": "太陽"})
```

### ChromaDB 批量寫入鎖定（向量索引建置）

ChromaDB PersistentClient 1.5.9 在逐檔 `collection.add()` 時可能觸發 Rust 內部鎖定（`readonly database` / `no such table: max_seq_id`）。**解法**：收集所有 chunks 後一次性寫入：

```python
# ❌ 逐檔寫入可能鎖死
for filepath in files:
    collection.add(embeddings=..., ids=...)

# ✅ 一次全部寫入
all_emb, all_ids, all_meta = [], [], []
for filepath in files:
    all_emb.extend(chunk_embs)
    all_ids.extend(chunk_ids)
    all_meta.extend(chunk_meta)
collection.add(embeddings=all_emb, ids=all_ids, metadatas=all_meta)
```

### Mem0 OSS 向量庫僅支援 Qdrant + PGVector
- **Qdrant**：本機檔案模式（`~/.hermes/mem0_qdrant/`），不需 server
- **PGVector**：需 PostgreSQL server
- ❌ ChromaDB、Milvus 不支援

### API Key 在 CLI 參數中被遮罩
Hermes 安全系統會對 CLI 參數中的 secret 內容實施 redaction，
導致 `--oss-llm-key sk-xxx` 在傳遞時被截斷成 `sk-xxx...xxx`，
造成 argparse 解析失敗。

**解法：** 先手動設環境變數再跑 setup
```bash
export OPENAI_API_KEY=sk-xxx
hermes memory setup mem0 --mode oss --oss-vector qdrant
```

### 參考資料
- Hermes 官方文件：[Memory Providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers)
- Provider 原始碼：`plugins/memory/<provider>/`
