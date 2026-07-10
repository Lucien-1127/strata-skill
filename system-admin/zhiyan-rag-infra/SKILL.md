---
name: zhiyan-rag-infra
description: 智研法律文件語意向量搜尋基礎設施 — RAG index 建置與搜尋
version: 1.2.0
author: zhiyan
tags:
  - zhiyan
  - RAG
  - vector-search
  - chromadb
  - bge-m3
  - embedding
  - local-embedding-server
status: stable
---

# zhiyan-rag-infra

智研法律文件 — Markdown 語意向量搜尋基礎設施。

以 **BAAI/bge-m3** + ChromaDB 建立本地向量索引，支援自然語言查詢。

---

## 專案位置

```
/home/ysga1/zhiyan-search/
├── build_index.py       # 索引建置
├── search.py            # 語意搜尋
├── config.yaml          # 共用設定
├── .env                 # HF Token（不進 git，HF 方式用）
├── requirements.txt
├── .gitignore
├── vector_store/        # ChromaDB 資料庫（不進 git）
└── README.md
```

---

## Embedding 提供方式

本基礎設施支援兩種 embedding 提供方式，擇一即可：

| 方式 | 依賴 | 優點 | 缺點 |
|:----|:-----|:-----|:-----|
| **本機 local embedding server (推薦)** | `freely.py` 或同類服務 (port 8008) | 無 rate limit、低延遲、完全離線 | 需常駐服務 |
| HuggingFace Inference API | HF Token + 網路 | 免本機 GPU | rate limit (~30 req/min)、需網路 |

> **⚠️ FreeLLM API (:3001) 不可用於 embedding** — 其上游 providers (OpenAI/text-embedding、Google/gemini-embedding) 全面被 GitHub/GCP 限流 429，無法可靠產出 embedding。

---

## 安裝

```bash
cd /home/ysga1/zhiyan-search
pip install -r requirements.txt
```

### 前置需求

- Python 3.10+
- 擇一：本機 embedding server (port 8008) **或** HuggingFace API Token
- zhiyan-legal repo 已 clone

---

## 設定

### config.yaml (本機 embedding server 方式)

```yaml
docs_path: /home/ysga1/zhiyan-legal/docs
api_base: http://localhost:8008/v1
api_key: freely-local
embedding_model: BAAI/bge-m3
vector_store_path: ./vector_store/
top_k: 5
```

### config.yaml + .env (HF Inference API 方式)

```yaml
docs_path: /home/ysga1/zhiyan-legal/docs
embedding_model: BAAI/bge-m3
vector_store_path: ./vector_store/
top_k: 5
# huggingface_token 從 .env 讀取
```

```bash
echo "HUGGINGFACE_TOKEN=hf_xxxxxxxxxx" > .env
```

> ⚠️ Token 必須放 `.env`，**不可寫入 config.yaml**。

---

## 使用

### 1. 啟動本機 embedding server（如使用此方式）

```bash
cd /home/ysga1/zhiyan-search
python freely.py          # 預設 :8008
FREELY_PORT=8009 python freely.py  # 自訂埠
```

端點：
- `GET  /v1/models` — 列出可用模型
- `POST /v1/embeddings` — OpenAI-compatible embedding API
- `GET  /health` — 健康檢查

### 2. 建索引

```bash
cd /home/ysga1/zhiyan-search
# 清除舊索引（首次或需重建時）
rm -rf vector_store/
# 執行建置
python build_index.py
```

**⚠️ 務必以 background 模式執行，否則會被 600s timeout 中斷：**

```
terminal(command="cd /home/ysga1/zhiyan-search && python build_index.py", background=true, notify_on_complete=true)
```

建索引是 CPU-bound + 網路 I/O，120 個檔案 ~1700 chunks 約需 3-5 分鐘。

支援增量更新 — 內容未變更的檔案自動跳過。

### 3. 搜尋

```bash
python search.py "Persona 骨架的安全規則"
```

JSON 輸出（供 pipe）：
```bash
python search.py "查詢" --json | jq .
```

---

## 技術架構

| 元件 | 選擇 | 理由 |
|:----|:-----|:-----|
| Embedding | **BAAI/bge-m3** via local server 或 HF API | 多語言（中英法律），1024 維 |
| 向量資料庫 | ChromaDB (PersistentClient) | 本機持久化，不需外部服務 |
| 分塊策略 | 按 Markdown 標題 + tiktoken 邊界 | 保留語意段落完整性 |
| 增量更新 | SHA256 檔案 hash 比對 | 避免重複 embedding 呼叫 |
| Token 計數 | tiktoken (cl100k_base) | 標準 tokenizer |
| API 協議 | OpenAI-compatible (`/v1/embeddings`) | 可換任意 provider |

### bge-m3 前綴策略

| 用途 | 前綴 |
|:----|:-----|
| 文件索引 | `Represent this sentence for searching relevant passages: ` |
| 查詢搜尋 | `Represent this query for searching relevant passages: ` |

> 前綴不符會大幅降低檢索品質 — 這是 bge 模型系列的已知特性。

---

## 建索引注意事項

### ChromaDB 中斷損毀（已知坑）

**症狀：**
```
chromadb.errors.InternalError: error returned from database: (code: 1032) attempt to write a readonly database
chromadb.errors.InternalError: no such table: max_seq_id
```

**原因：** ChromaDB 的 Rust SQLite backend 在 SIGTERM 中斷時會留下半寫入狀態，下次讀取時無法正常初始化內部表。

**解決：** 唯一解法是刪除 `vector_store/` 整個目錄並重建：
```bash
rm -rf /home/ysga1/zhiyan-search/vector_store/
python build_index.py
```

**預防：** 避免 foreground mode 被 timeout 殺掉 — 永遠用 background mode。

### FreeLLM API :3001 embedding 全面不可用

所有 `text-embedding-*` 系列（small/large/auto）在 FreeLLM API 上都被上游 provider 限流：
- `text-embedding-3-small` → GitHub 429
- `text-embedding-3-large` → GitHub 429
- `auto` → 路由至 gemini-embedding-001 → Google quota 429

**解法：** 改用本機 embedding server (port 8008) 或 HF Inference API。

### batch_embed 必須有重試邏輯

不論用哪種 embedding 提供方式，`batch_embed` 都應加入指數退避重試：

```python
def batch_embed(texts, client, model, batch_size=8):
    import time
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        for attempt in range(5):
            try:
                response = client.embeddings.create(model=model, input=batch)
                # ... process response
                break
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    time.sleep(2 ** attempt)  # 1, 2, 4, 8, 16s
                else:
                    raise
```

### 批次大小建議

| 設定 | 情境 |
|:----|:-----|
| batch_size=8 | HF Inference API（rate limit 敏感） |
| batch_size=16 | 本機 server（無 rate limit） |

---

## 常見問題

**Q: 為什麼不用本機 sentence-transformers？**
A: 這台 VM 只有 2 vCPU / 8GB RAM，bge-m3 (568M params) 本機推理極慢（~3-8s/chunk），且常駐佔 2-4GB RAM。本機 embedding server 透過 freely.py 包裝後仍是遠端調用，不佔 VM 推理資源。

**Q: 可以換模型嗎？**
A: config.yaml 改 `embedding_model` 即可，但需注意：
- 維度變更需清空 `vector_store/` 重建索引
- bge 系列需要對應的前綴策略

**Q: 如何清除索引重建？**
```bash
python3 -c "import shutil,os; shutil.rmtree('/home/ysga1/zhiyan-search/vector_store/'); os.makedirs('/home/ysga1/zhiyan-search/vector_store/')"
python build_index.py
```
> 不要用 `rm -rf` — 安全審計會擋。

---

## 相關文件

- `references/bge-m3-strategy.md` — bge-m3 模型策略、前綴規則與替代模型
- `references/incremental-indexing.md` — 增量索引機制與子代理執行模式
- `references/freely-routing.md` — freely 本地路由服務與 Colab GPU tunnel 方案
