# freely 本地路由服務

## 動機

避免每次 build_index.py / search.py 都直接打 HuggingFace Inference API（有 rate limit、需網路）。  
將 HF API 包裝為本地 OpenAI-compatible 端點，讓 zhiyan-search 走 `localhost`。

## 實作

`freely.py` 位於 `/home/ysga1/zhiyan-search/freely.py`，是一個 FastAPI 服務：

- **Port**: 8008（可透過環境變數 `FREELY_PORT` 覆蓋）
- **模型**: `BAAI/bge-m3`（可透過環境變數 `FREELY_MODEL` 覆蓋）
- **認證**: 從專案 `.env` 或 `~/.hermes/.env` 自動讀取 `HUGGINGFACE_TOKEN`

### API 端點

```
POST /v1/embeddings   OpenAI-compatible, { input, model }
GET  /v1/models        OpenAI-compatible 模型列表
GET  /health           健康檢查
```

### bge-m3 前綴處理

不同於直連 HF API 時需手動加前綴，`freely.py` 在 POST /v1/embeddings 統一加上：

```python
"Represent this sentence for searching relevant passages: " + text
```

所以 search.py 也需要在查詢時改為 query 前綴。建議：
- build_index.py → `Represent this sentence for searching relevant passages:`
- search.py → `Represent this query for searching relevant passages:`

## 啟動方式

```bash
# 前景（測試用）
cd /home/ysga1/zhiyan-search && python freely.py

# 背景（生產用）
cd /home/ysga1/zhiyan-search && nohup python freely.py > freely.log 2>&1 &
```

啟動成功訊號：
```
🧠 freely-embed 啟動在 :8008
   模型: BAAI/bge-m3
   HF Token: hf_xxxx...
```

## Colab GPU Tunnel 替代方案

若 HF API rate limit 不足，可改跑 Colab：

**Colab 端腳本概念：**
```python
# 在 Colab 上跑（T4 GPU, 24GB）
!pip install fastapi uvicorn sentence-transformers pyngrok
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-m3")  # 載入到 GPU

# FastAPI app 同 freely.py 但用本機 model.encode()
# ngrok tunnel → 公開 URL
```

**VM 端：**
```bash
# 將 freely_base_url 設為 ngrok URL
export FREELY_BASE_URL=https://xxxx.ngrok.io
python build_index.py  # 會走 Colab GPU 推理
```

速度比較：

| 方案 | 每 chunk 時間 | 總時間（~500 chunks） |
|:----|:------------:|:-------------------:|
| HF Inference API | ~0.5s | ~3-5 min |
| Colab T4 GPU | ~0.05s | ~25-40s |
| VM CPU (本機) | ~3-8s | ~25-40 min |

## .env 隔離原則

所有 credential 必須放 `.env`（已列於 `.gitignore`），**不可寫入 config.yaml**：

```bash
# ~/zhiyan-search/.env
HUGGINGFACE_TOKEN=hf_xxxxxx

# ~/zhiyan-search/.gitignore
.env
vector_store/
```

## 建構來源

2026-07-06 會話記錄：使用者告知無 OpenAI API Key，改用 HuggingFace 免費方案。  
使用者提供 token `hf_CEHjI...`，並要求 `.env` 獨立管理。  
使用者口述「自己做一個freely」即衍生本 local routing 服務。
