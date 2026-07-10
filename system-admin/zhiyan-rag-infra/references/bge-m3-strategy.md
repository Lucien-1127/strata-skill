# bge-m3 嵌入策略備忘

## 模型基本資訊

- **模型**: BAAI/bge-m3
- **維度**: 1024
- **參數**: 568M
- **語言**: 多語言（中英混合優異）
- **存取**: HuggingFace Inference API（免費帳號可用）

## 前綴策略（關鍵！）

bge-m3 在 embedding 前需要加特定前綴，否則檢索品質會大幅下降：

```python
# 文件索引時（build_index.py）
"Represent this sentence for searching relevant passages: " + doc_text

# 查詢搜尋時（search.py）
"Represent this query for searching relevant passages: " + query_text
```

## 為什麼選 API 而非本機

| 方案 | 推理速度 | RAM 佔用 | 費用 |
|:----|:-------:|:--------:|:----:|
| HF Inference API | ~0.5s/chunk | 0 | 免費（有 rate limit） |
| sentence-transformers 本機 | ~3-8s/chunk | 2-4GB | 0 |

本機推理在 2 vCPU VM 上太慢且會與 Hermes gateway 搶資源。

## HF API 使用限制

- 批次建議 ≤ 8 個 texts/call
- Rate limit：免費帳號約 30 req/min
- 若回傳 503/429，重試 1-3 次可恢復
- Token 透過環境變數或 `.env` 傳遞，**不寫入 config.yaml**

## 替代模型（同類 API）

若未來 bge-m3 有問題，可換：

| 模型 | 維度 | 語言 |
|:----|:---:|:----|
| intfloat/multilingual-e5-large | 1024 | 多語言 |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | 384 | 多語言（更快但較弱） |
