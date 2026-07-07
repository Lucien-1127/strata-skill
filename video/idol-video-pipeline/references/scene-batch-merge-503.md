# 場景批次生成 & 合併 & 503 重試

## 情境

已有一組場景的圖片（如場景①），需追加更多場景（如②③④），並合併為完整結果集。

## 批次生成腳本結構

寫一個獨立 Python 腳本（非 delegate_task），直接叫 API：

```python
#!/usr/bin/env python3
import base64, json, os, sys, time, urllib.request, urllib.error

API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
API_KEY = os.environ.get("AGNES_API_KEY")  # 或從 ~/.hermes/env/agnes.env 讀取

# 1. 讀取參考圖
with open("reference.jpg", "rb") as f:
    data_uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

# 2. 定義場景列表
scenes = [
    {"name": "② 主歌 — 深情歌唱", "prompt": "...", "negative": "..."},
    {"name": "③ 副歌 — 熱情舞蹈", "prompt": "...", "negative": "..."},
]

# 3. 逐場景生成（間隔 2 秒）
results = []
for s in scenes:
    for attempt in range(5):
        try:
            resp = call_api(s["prompt"], s["negative"], data_uri)
            url = json.loads(resp.read())["data"][0]["url"]
            results.append({"name": s["name"], "url": url})
            break
        except urllib.error.HTTPError as e:
            if e.code == 503:
                time.sleep(2 ** (attempt + 1))
            else:
                raise
    time.sleep(2)
```

## 與既有結果合併

```python
# 讀取既有結果檔
try:
    with open("/tmp/idol_images.json") as f:
        existing = json.load(f)
    scene1 = existing["results"]
except FileNotFoundError:
    scene1 = []

# 新場景
scene2_to_4 = results  # 批次生成的結果

# 合併
all_results = scene1 + scene2_to_4
output = {"results": all_results, "total": len(all_results)}

# 寫入
with open("/tmp/idol_all_images.json", "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
```

## 場景定義慣例

場景物件格式：

```json
{
  "name": "② 主歌 — 深情歌唱",
  "url": "https://platform-outputs.agnes-ai.space/images/i2i/<32hex>/output.png"
}
```

輸出檔結構：

```json
{
  "results": [
    {"name": "① 開場 — 舞台登場", "url": "..."},
    {"name": "② 主歌 — 深情歌唱", "url": "..."},
    ...
  ],
  "total": 4
}
```

## 已知問題

| 問題 | 對策 |
|------|------|
| 503 Service Unavailable | 指數退避重試（2/4/8/16/32s × 5 次） |
| base64 過長使輸出難以閱讀 | `url[:80]` 截斷顯示，不 print 完整 URL |
| 場景④生成比前幾個更容易 503 | 推測是因為靠後的請求在排隊，優先先前的請求 |
| 腳本中途 crash 未存檔 | 每成功一個場景就 append 到暫存檔，不要全部在最後才寫 |
