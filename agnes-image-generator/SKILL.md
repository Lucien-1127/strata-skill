---
name: agnes-image-generator
description: Generate images via Agnes Image 2.1 Flash (text-to-image + image-to-image using img2img), with 503 retry logic and structured output merging.
version: 2.0.0
author: Hermes
platforms: [linux]
status: stable
---

# Agnes Image 2.1 Flash — 圖片生成

## 觸發方式

直接請求：「用 Agnes 生一張圖」、「img2img 保持角色一致性」、「場景②③④」

## 環境準備

- API Key: `~/.hermes/env/agnes.env` → `AGNES_API_KEY`（由 agnes-quota-router 管理）
- 端點: `POST https://apihub.agnes-ai.com/v1/images/generations`
- 模型: `agnes-image-2.1-flash`
- 無需 pip 安裝任何套件 — 用 `urllib.request` 即可（Python 內建模組）

## Text-to-Image

```python
import json, urllib.request

payload = {
    "model": "agnes-image-2.1-flash",
    "prompt": "Anime idol on stage, colorful lights, confetti",
    "size": "576x1024",    # 9:16 直式
    "n": 1,
}
resp = urllib.request.urlopen(urllib.request.Request(
    "https://apihub.agnes-ai.com/v1/images/generations",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
))
body = json.loads(resp.read())
url = body["data"][0]["url"]
```

## Image-to-Image (img2img) — 角色一致性

保持角色一致的關鍵：**使用原始參考圖作為 `extra_body.image`**（Base64 Data URI）。

```python
import base64, json, urllib.request

# 讀取參考圖 → Base64 Data URI
with open("reference.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
data_uri = f"data:image/jpeg;base64,{b64}"

payload = {
    "model": "agnes-image-2.1-flash",
    "prompt": "Close-up portrait, singing into microphone, same character as reference",
    "negative_prompt": "different character, face change, different hairstyle, different outfit, "
                       "different person, character mutation, face morphing, identity change, "
                       "distorted face, ugly, deformed, bad anatomy, blurry, inconsistent character",
    "size": "576x1024",
    "n": 1,
    "extra_body": {
        "image": data_uri   # ✅ 單字串（Base64 Data URI）
    }
}
```

**注意**：
- `extra_body.image` 是**單一字串**（Base64 Data URI 或公開 URL），**不是陣列**
- 圖生影的 `image` 參數只接受公開 URL（不接受 Base64）— 見 agnes-quota-router

## 批次生成多場景

當用戶需要多張場景圖（如 3-4 個分鏡），**寫一個 Python 腳本一次性呼叫**：

```python
scenes = [
    {"name": "② 主歌 — 深情歌唱", "prompt": "...", "negative": "..."},
    {"name": "③ 副歌 — 熱情舞蹈", "prompt": "...", "negative": "..."},
]
results = []
for scene in scenes:
    resp = call_agnes(scene["prompt"], scene["negative"])
    results.append({"name": scene["name"], "url": body["data"][0]["url"]})
    time.sleep(2)  # 避免速率限制
```

## 503 服務繁忙 — 重試策略

Agnes 偶發 503（`ServiceUnavailableError: image generation service is busy`）。

**必須用指數退避重試**：

```python
import time

for attempt in range(5):
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        break  # 成功
    except urllib.error.HTTPError as e:
        if e.code == 503:
            wait = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32 秒
            print(f"503, waiting {wait}s...")
            time.sleep(wait)
        else:
            raise
```

- 上限：5 次重試（約 62 秒最長等待）
- 其他 HTTP 錯誤不重試（可能要求金鑰過期等）
- 首次成功率約 ~60-70%，重試後 ~95%

## 場景結果合併

當新生成的場景需要與既有的結果合併時：

```python
# 讀取既有結果
with open("/tmp/idol_images.json") as f:
    existing = json.load(f)

# 新場景（新生成的圖）
new_scenes = [{"name": "④ 尾聲 — 感謝鞠躬", "url": "..."}]

# 合併
all_results = existing["results"] + new_scenes

# 保存
with open("/tmp/idol_all_images.json", "w") as f:
    json.dump({"results": all_results, "total": len(all_results)}, f, ensure_ascii=False, indent=2)
```

## 回應解析

API 回應結構：

```json
{
  "created": 1234567890,
  "data": [{"url": "https://platform-outputs.agnes-ai.space/images/i2i/.../output.png"}],
  "usage": {...}
}
```

URL 欄位：`body["data"][0]["url"]`
備用欄位：`b64_json`（如有設定 `return_base64: true`）

## 支援尺寸

- `576x1024` (9:16 直式推薦 — 角色圖用這個)
- `1024x576` (16:9 橫式)
- `1024x768`, `768x1024`
- `1024x1024`, `1920x1080`, `1080x1920`

## Pitfalls

- ❌ **不要用 Windows 路徑** (`/c/Users/...`) — 所有路徑用 Linux 格式
- ❌ **不要硬編碼 API key** — 從 `~/.hermes/env/agnes.env` 讀取 `AGNES_API_KEY`
- ❌ **不要用 `sk-nous-*` 或舊版 key** — 目前的 key 是 `cpk-*` 格式
- ❌ **Base64 過長時不要 print 完整內容** — 用 f-string 截斷 (`[:80]`) 避免輸出淹沒
- ✅ 批次生成時 **每次 API 呼叫間隔 2+ 秒**避免速率限制
- ✅ 503 一定用指數退避重試
- ✅ 角色保留的負面提示詞要包含完整的面部/身形約束
- ✅ 最終結果存為 JSON 格式（`/tmp/xxx_images.json`），方便後續流水線取用
