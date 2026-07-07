# v5 完整腳本參考

這份腳本是本 session 最終驗證通過（零重疊、零跨頁）的完整 PDF 生成腳本。
位於 `/home/ysga1/generate_master_pdf.py`（當前 VM），但引用時請以 skill 目錄為基準。

## 結構

| 區塊 | 行數 | 說明 |
|:-----|:----:|:------|
| 初始化 | ~40 | PDF 類別定義、字型載入、排版常數 |
| 輔助函數 | ~80 | need, heading, item, body, bold, hr, law_box, tbl |
| 封面 | ~25 | 封面頁 |
| 摘要 | ~20 | 摘要框 |
| 第一章 | ~30 | 預告登記 (5 items) |
| 第二章 | ~20 | 代書框架 (4 items) |
| 第三章 | ~20 | 三性觀察 (3 items + 1 law_box) |
| 第四章 | ~20 | 上市櫃 (4 items + 1 law_box) |
| 第五章 | ~30 | 綜合整理 (tbl + item) |
| 參考資料 | ~15 | refs list |
| 末頁填充 | ~25 | 附錄 + 半頁填充 + 免責 |

## 關鍵：item() 的排版演進

```
v1: cell(42) + multi_cell(0)        → 第二行 LMARGIN 重疊
v2: multi_cell(0) + multi_cell(0)   → 同 Y 重疊
v3: write() 流式                    → CJK 溢排
v4: cell(42) + multi_cell(108)      → CJK 溢排 cell 邊界
v5: multi_cell(0) 兩行分開           → 不同 Y 零重疊 (最終解法)
```

## 驗證結論（pdftoppm 像素分析）

```
排除表格深色背景(>85%暗)後：
第1頁: 真正重疊=0行
第2頁: 真正重疊=0行
第3頁: 真正重疊=0行
第4頁: 真正重疊=0行

注意：表格標題列 NAVY(20,40,85) 背景約 91% 暗
→ 若未排除 >85% 全暗行，會被誤判為重疊
→ 驗證腳本必須加 `if dark > 0.85: continue`
```
