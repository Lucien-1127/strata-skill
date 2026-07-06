# 持久化記憶 RAG 架構

> 來源：老闆知識庫

## 核心命題

RAG 從「可用」到「可靠」的關鍵：利用歷史互動、用戶偏好與過往檢索結果。

## 分層架構

| 層 | 職責 | 技術 |
|:---|:------|:------|
| SQLite | 結構化記憶、狀態、歷史、元數據索引 | 關聯式查詢 |
| ChromaDB | 向量嵌入、語義檢索 | 相似性搜尋 |

> ChromaDB 負責「找什麼」(What)，SQLite 負責「為誰找、何時找」(Who, When, Why)

## 智慧檢索流程

1. 從 SQLite 載入記憶上下文
2. 合成增強型查詢向量（融合歷史）
3. ChromaDB 多路徑檢索（文件庫 + QA 記憶庫）
4. 根據權重重排序
5. 將檢索過程記錄回 SQLite

## 對應 strat 系統

- SQLite 記憶層 → strat-memory-policy 內容分級 + 壓縮
- ChromaDB 檢索 → 未來整合至 Anchor 階段
- 檢索日誌 → strat-memory-policy 的壓縮報告
