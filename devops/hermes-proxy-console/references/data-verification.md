# Mini App 數據真實性驗證

## 背景

老闆極度厭惡虛假數據（"你又在騙我了"）。Mini App 儀表板上任何數字都必須能追溯到後端真實資料來源。

## 驗證金字塔（由快至慢）

### L1: API 端點直接驗證

```bash
# 取得 JWT token
TOKEN=$(curl -s -X POST http://localhost:8081/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"Ting7809"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# 驗證各端點有真實資料
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8081/api/proxy/status | python3 -m json.tool
```

關鍵檢查：`stats.total_requests > 0` ∧ `stats.error_rate` 是合理數字（非 null/NaN）

### L2: 資料庫直接查詢

Mini App 後端讀取 FreeLLM 的 SQLite DB：

```bash
DB="/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db"

# 總請求 vs 錯誤數
sqlite3 "$DB" "SELECT COUNT(*) as total, SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as errors FROM requests;"

# 錯誤分類（找根因）
sqlite3 "$DB" "SELECT error, COUNT(*) as cnt FROM requests WHERE status='error' GROUP BY error ORDER BY cnt DESC LIMIT 10;"
```

### L3: 前端渲染交叉比對

在瀏覽器 console（登入後）：
```js
// 檢查背景色
getComputedStyle(document.body).background  // → rgb(15, 23, 42)
// 檢查 JS 錯誤
// (browser_console 工具)
```

## 常見虛假數據信號

| 信號 | 說明 |
|---|---|
| 數字都是整數（如 `error_rate: 50` 而非 `53.2`） | 疑為硬編碼 |
| 刷新後數字完全沒變 | 疑為 mock data |
| 某區塊顯示「暫無資料」但資料庫有對應記錄 | API 端點未正確接上 |
| 前端顯示的數字與 `curl` API 回傳不一致 | adapter 層轉換錯誤 |

## 實例：本次 ProxyPage 驗證

用戶看到 `1,664 錯誤數 / 53.2% 錯誤率`，透過 L2 直接查 DB 確認：

```
總請求|3128
錯誤數|1664
錯誤率(%)|53.2
```

→ 完全匹配，且發現 62.5% 錯誤來自 GitHub 自訂模型的 429 限流。
