---
name: legal-db-ai-fill
description: "批次填寫 Legal_DB_Full_Part1 試算表的 AI 欄位（白話摘要、實務爭點、關鍵字Tags、關聯條文），含品質修正工作流"
---
# legal-db-ai-fill

## 📖 Description

批次填寫 Legal_DB_Full_Part1 試算表的 AI 欄位（白話摘要、實務爭點、關鍵字Tags、關聯條文），含品質修正工作流

---

# Legal_DB AI 填寫技能

用多代理平行處理的方式，批次填寫 Google Sheets 中法律條文的 AI 生成欄位。

## 適用場景

- **Legal_DB_Full_Part1** 試算表中的空白 AI 欄位（商事法、勞動社會法等）
- 修正已填欄位的品質（實務爭點太籠統、關聯條文缺失、白話摘要不精確）
- 主表位置：`1KqOzeH3Dg_bdOt23oO24SQAalQgY2ZcWGvhHOM_k7rA`

## 前置條件

1. Google Workspace skill 已安裝且認證通過
2. Google Sheets API 已啟用
3. 目標試算表 ID 已知

## 工作流

### 第一步：檢查進度

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json, os

token_path = "C:/Users/ysga1/AppData/Local/hermes/google_token.json"
with open(token_path) as f:
    cred_data = json.load(f)

creds = Credentials.from_authorized_user_info(cred_data)
sheets_service = build("sheets", "v4", credentials=creds)
drive_service = build("drive", "v3", credentials=creds)

MASTER = "1KqOzeH3Dg_bdOt23oO24SQAalQgY2ZcWGvhHOM_k7rA"

# 檢查指定分頁的填寫進度
def check_progress(sheet_name):
    data = sheets_service.spreadsheets().values().get(
        spreadsheetId=MASTER,
        range=f"'{sheet_name}'!F:F"
    ).execute()
    vals = data.get("values", [])
    total = len(vals) - 1
    filled = sum(1 for r in vals[1:] if r and r[0].strip())
    return filled, total

for sheet in ["商事法", "勞動社會法", "憲法", "民法", "刑法", "行政法", "小法及其他"]:
    try:
        f, t = check_progress(sheet)
        print(f"{sheet}: {f}/{t} ({f/t*100:.0f}%)")
    except:
        pass

# 檢查「適用範圍明確」佔比
def check_vague_issues(sheet_name):
    data = sheets_service.spreadsheets().values().get(
        spreadsheetId=MASTER,
        range=f"'{sheet_name}'!G:G"
    ).execute()
    vals = data.get("values", [])
    total = len(vals) - 1
    vague = sum(1 for r in vals[1:] if r and "適用範圍明確" in r[0])
    return vague, total
```

### 第二步：批次填寫（填充空白）

使用 `delegate_task` 平行處理，每次派 3 個子代理：

```python
# 讀取一批條文
def read_batch(sheet_name, start_row, count=60):
    end_row = start_row + count - 1
    data = sheets_service.spreadsheets().values().get(
        spreadsheetId=MASTER,
        range=f"'{sheet_name}'!A{start_row}:E{end_row}"
    ).execute()
    vals = data.get("values", [])
    
    lines = []
    for i, v in enumerate(vals):
        if len(v) >= 5:
            row = start_row + i
            lines.append(f"[{row}] ID:{v[0]} {v[3]}: {v[4]}")
    
    return "\n".join(lines), len(vals)
```

然後用 `delegate_task` 呼叫子代理，**每個子代理處理 60 條**。

**子代理提示詞範本（低溫設定）：**

```
溫度最低。嚴格忠於原文。對每一條條文，輸出：
- 白話摘要（2-3句平易中文）
- 實務爭點（1-2句具體爭議點，不要寫「適用範圍明確」）
- 關鍵字Tags（4-6個空格分隔）
- 關聯條文（具體法條號，不要空白）

輸出純 JSON array，格式：
[{"row": 行號, "summary": "...", "issue": "...", "tags": "...", "related": "..."}, ...]
```

### 第三步：品質修正（改善已填欄位）

當「實務爭點」欄位出現過多「適用範圍明確，較少實務爭議」時：

1. 先掃描整個分頁找出問題行
2. 用子代理批次修正，每批 60 條
3. 要求子代理針對每條條文的具體內容提供：
   - 相關的大法官解釋/判例
   - 學說爭議
   - 實務適用上的常見問題
   - 條文間的關聯性

**修正提示詞重點：**
```
實務爭點：把「適用範圍明確，較少實務爭議」改為具體的實務爭議
關聯條文：把「無」改為相關的憲法條文號、大法官解釋號、或相關法律名稱
白話摘要：如已夠好則保留，不足則微調
```

### 第四步：寫回試算表

```python
# 子代理回傳的 JSON 寫入
def write_batch(fixes, sheet_name):
    fixes.sort(key=lambda x: x.get("row", 9999))
    values = [[f.get("summary",""), f.get("issue",""), f.get("tags",""), f.get("related","")] for f in fixes]
    
    start_row = fixes[0]["row"]
    end_row = fixes[-1]["row"]
    
    body = {"values": values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=MASTER,
        range=f"'{sheet_name}'!F{start_row}:I{end_row}",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"✅ 寫入 rows {start_row}~{end_row}")
```

## 批次策略

| 策略 | 數量 | 時間 |
|:----|:---:|:----:|
| 3 子代理 × 60 條 | 180 條/波 | ~8 分鐘 |
| 3 子代理 × 100 條 | 300 條/波 | ~15 分鐘 |

## 剩餘工作量（截至 2026-06-20）

| 分頁 | 剩餘 | 預估波數 |
|:----|:---:|:--------:|
| 商事法 | 620 條 | ~4 波 |
| 勞動社會法 | 287 條 | ~2 波 |
| 小法及其他（爭點修正） | 1,022 條 | ~6 波 |
| Legal_DB_Full_Part1（爭點修正） | 1,193 條 | ~7 波 |

## 注意事項

1. **溫度最低**：產出法律 AI 內容時，始終要求低溫、忠於原文、禁止發揮
2. **速率限制**：Google API 有 userRateLimitExceeded，每次呼叫後等待 1.5~2.5 秒
3. **Windows 路徑**：token 路徑為 `C:/Users/ysga1/AppData/Local/hermes/google_token.json`
4. **Hermes 設定**：delegation.max_concurrent_children = 3（最多 3 平行）
5. **子代理環境**：子代理無法直接讀取本機檔案，條文資料需透過 context 傳入
6. **JSON 格式**：子代理輸出必須是純 JSON array，不可有 Markdown 包裝
