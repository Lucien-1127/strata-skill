# FreeLLM SQLite → Miniapp SQLite 資料遷移

## 來源 DB 位置

FreeLLM 執行於 Docker container `zhiyan-freellmapi-1`，DB 位於 host volume：

```bash
sudo cp /var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db /tmp/freellm.db
sudo chmod 644 /tmp/freellm.db
```

## 關鍵結構差異

| 層級 | FreeLLM (`freeapi.db`) | Miniapp (`miniapp.db`) |
|------|------------------------|------------------------|
| 模型 | `models` 表：唯一鍵 `(platform, model_id)` | `models` 表：`name` 欄位為 `{platform}/{model_id}` |
| 金鑰→模型關聯 | `requests` 表：`model_id` 為 **字串**（非 DB id），搭配 `platform` 定位模型 | `api_entries` 表：`model_id` 為 **外鍵整數** |

## 遷移陷阱

### 陷阱 1：`requests.model_id` 是字串，不是 models.DB id

```sql
-- FreeLLM requests 表
SELECT key_id, platform, model_id FROM requests LIMIT 3;
-- 結果: 1|gemini-2.5-flash  (model_id 是字串 "gemini-2.5-flash"，不是 models 表的 id!)

-- 正確的模型查詢方式：用 (platform, model_id) 組合鍵
SELECT id FROM models WHERE platform='gemini' AND model_id='gemini-2.5-flash';
```

### 陷阱 2：models 表曾經重建，id 從 63+ 開始

FreeLLM 的 `models` 表曾重建導致 id 不連續。不要硬編碼 id 範圍。

## 遷移腳本核心邏輯

```python
# Step 1: 建立 (platform, model_id) → new_id 的 lookup
models_lookup = {}
for platform, model_id, enabled in src.execute("SELECT platform, model_id, enabled FROM models"):
    name = f"{platform}/{model_id}"
    dst.execute("INSERT INTO models (name, provider, enabled) VALUES (?, ?, ?)", (name, platform, enabled))
    models_lookup[(platform, model_id)] = dst.lastrowid

# Step 2: 用 requests 表的 (platform, model_id) 去查 models_lookup
key_model_counts = src.execute("""
    SELECT r.platform, r.model_id, r.key_id, count(*) as cnt
    FROM requests r WHERE r.key_id IS NOT NULL
    GROUP BY r.platform, r.model_id, r.key_id
""").fetchall()

# Step 3: 每個 key 取其用量最多的 model
key_best = {}
for platform, model_id, key_id, cnt in key_model_counts:
    if key_id not in key_best or cnt > key_best[key_id][0]:
        key_best[key_id] = (cnt, platform, model_id)

# Step 4: 查 endpoint = api_keys.base_url
key_info = {}
for key_id, platform, base_url in src.execute("SELECT id, platform, base_url FROM api_keys"):
    key_info[key_id] = {"endpoint": base_url or f"api.{platform}.com"}

# Step 5: 寫入 api_entries
for key_id, (cnt, platform, model_id) in key_best.items():
    new_model_id = models_lookup.get((platform, model_id))
    if not new_model_id:
        continue
    dst.execute("INSERT INTO api_entries(model_id, endpoint, key_alias, quota_limit, usage, rate_limited) VALUES(?,?,?,?,?,?)",
        (new_model_id, key_info[key_id]["endpoint"], f"key_{key_id}", 1000, cnt, rate_limited))
```

## 驗證遷移結果

```bash
# 確認模型數和條目數
sqlite3 /home/ysga1/hermes-miniapp/data/miniapp.db \
  "SELECT 'models', count(*) FROM models UNION ALL SELECT 'entries', count(*) FROM api_entries"

# 確認 dashboard API 回傳正確筆數
TOKEN=$(curl -sk -X POST https://lucien126.com/m/api/auth/login \
  -H 'Content-Type: application/json' -d '{"password":"***"}' | jq -r '.data.token')
curl -sk https://lucien126.com/m/api/dashboard -H "Authorization: Bearer $TOKEN" | jq '.data | length'
curl -sk https://lucien126.com/m/api/entries -H "Authorization: Bearer $TOKEN" | jq '.data | length'
```
