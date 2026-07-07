# 偶像演唱會 — 圖生影提示詞完整範例

這是 session 2026-07-06 實測驗證過的 prompt 組合，用於生圖→圖生影→串接的完整流水線。

## 角色參考圖

來源：用戶提供的動畫偶像角色圖（720×1280, 9:16 直式）
處理方式：base64 Data URI → `extra_body.image: [data_uri]`（img2img，不走預處理）

## 場景腳本（4 場景 × 5 秒）

### ① 開場 — 舞台登場
**圖片 prompt：**
```
Anime idol girl standing on illuminated concert stage, dramatic spotlight from above creating rim light, stage fog, holding microphone, confident looking at audience, blue purple stage lighting, cinematic angle, same character as reference
```
**影片 prompt：**
```
Anime idol girl standing on illuminated stage, spotlight from above creating dramatic rim light, stage fog gently rolling, microphone in hand, looking confidently at audience, concert atmosphere with blue and purple stage lights, cinematic angle, professional concert footage style
```

### ② 主歌 — 深情歌唱
**圖片 prompt：**
```
Close-up portrait of anime idol girl singing into microphone, eyes half-closed emotion, gentle smile, warm amber backlight, bokeh background, emotional style, same character as reference
```
**影片 prompt：**
```
Close-up of anime idol singing into microphone, eyes half-closed with emotion, gentle smile, stage lights creating soft glow on face, warm amber backlight, bokeh background lights, emotional music video feel
```

### ③ 副歌 — 熱情舞蹈
**圖片 prompt：**
```
Dynamic mid-shot of anime idol dancing on stage, hair flowing, colorful stage lights, confetti, happy expression, choreography pose, concert climax, same character as reference
```
**影片 prompt：**
```
Anime idol dancing energetically, hair flowing with motion, colorful stage lights flashing rainbow colors, confetti falling, happy energetic expression, choreography pose, concert climax atmosphere
```

### ④ 尾聲 — 感謝鞠躬
**圖片 prompt：**
```
Wide concert stage, anime idol bowing to audience with grateful smile, golden warm lighting, audience silhouette, confetti settling, emotional finale, same character as reference
```
**影片 prompt：**
```
Anime idol bowing to audience with grateful smile, all stage lights focused on center stage, golden warm lighting, audience silhouette in background, confetti settling, emotional finale moment, cinematic closing shot
```

## 通用負面提示詞（角色保留）

所有 4 場景共用，不可省略：

```
different character, face change, identity change, face morphing,
different hairstyle, different outfit, appearance drift,
character mutation, swapped identity, face distortion,
inconsistent character, ugly, deformed, bad anatomy,
blurry, jittery, distorted, low quality
```

## 參數設定

| 參數 | 圖片 | 影片 |
|:----|:----|:----|
| model | agnes-image-2.1-flash | agnes-video-v2.0 |
| size | 576×1024 | 576×1024 |
| num_frames | - | 121 (8n+1 規則) |
| frame_rate | - | 24 |
| image input | extra_body.image [base64 data URI] | image [public URL from img output] |

## 失敗經驗

| 問題 | 原因 | 解法 |
|:----|:-----|:-----|
| 角色跑掉 | img2img 預處理改了角色 | 直接用原圖 base64，不走預處理 |
| 角色漂移 | 影片 prompt 沒加保留詞 | 加角色保留負面提示詞 |
| 比例歪成 4:3 | 沒設 width/height | 固定 576×1024 (9:16) |
| 輪詢 timeout | 300 秒不夠 | 改 600 秒 |
| url 取不到 | 用了 `remixed_from_video_id` | 改用 `data.get("url", "")` |
