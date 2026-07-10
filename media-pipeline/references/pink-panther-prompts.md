# 頑皮豹 5 場景動畫 — 實測驗證提示詞

2026-07-08 實測，使用 Agnes Video V2.0 + 角色參考圖模式。
全部 5 場景共用同一張參考圖，輸出 23.5 秒，角色一致性良好。

## 參考圖片

```
Ref: https://platform-outputs.agnes-ai.space/images/t2i/820dd08f8ab24c47a23770d028a9a691.png
```
Prompt: "Pink Panther character full body standing pose, elegant cool confident posture, sleek pink cartoon panther, long thin tail curved, white gloves, minimalist white background, classic 1960s animation style, simple clean lines, flat cel-shaded vector art style, character reference sheet quality, sharp outlines, solid colors, no shading, iconic design"

## 三層提示詞結構

所有場景提示詞遵循：**保留層 → 動態層 → 場景層**

| 層 | 功能 | 範例 |
|---|---|---|
| 保留層 | 定義什麼不動 | `keeping face, body shape, pink color, tail, and white gloves identical to the reference image` |
| 動態層 | 最小必要 motion | `character slowly walking forward with cool confident swagger, shoulders gently swaying` |
| 場景層 | 背景/燈光/運鏡 | `minimalist white background, camera slowly dolly in` |

## 5 場景提示詞

### 場景 1: 開場 — 經典踱步登場
```
keeping face, body shape, pink color, tail, and white gloves identical to the reference image, character slowly walking forward with cool confident swagger, shoulders gently swaying, tail curling slightly, camera slowly dolly in, minimalist white background
```

### 場景 2: 巧遇 — 好奇窺探
```
keeping face, body shape, pink color, tail, and white gloves identical to the reference image, character slowly turning head to peek around corner, ears twitching slightly, eyes narrowing curiously, subtle breathing, warm window light from left, simple room background
```

### 場景 3: 惡作劇 — 油漆意外
```
keeping face, body shape, pink color, tail, and white gloves identical to the reference image, pink paint slowly dripping from above, character looking up in surprise, paint splashing on floor, subtle body recoil, colorful paint drops falling, white room background
```

### 場景 4: 追逐 — 門廊穿梭
```
keeping face, body shape, pink color, tail, and white gloves identical to the reference image, character walking briskly through corridor with many doors, doors gently opening and closing behind, cool relaxed expression, confident stride, warm golden lighting, long hallway perspective
```

### 場景 5: 收尾 — 從容離去
```
keeping face, body shape, pink color, tail, and white gloves identical to the reference image, character walking away from camera down street, iconic cool swagger with swaying shoulders, long shadow stretching forward, tail gently swaying, warm sunset backlight, cinematic silhouette
```

## 執行指令

```bash
# 方式一：角色參考圖模式（推薦）
python3 scripts/idol-video.py \
  --ref-image "https://platform-outputs.agnes-ai.space/images/t2i/820dd08f8ab24c47a23770d028a9a691.png" \
  --scenes-file references/pink-panther-prompts.json \
  --scenes 5 --duration 5 --crossfade

# 方式二：無 crossfade（避開 xfade bug，較穩定）
python3 scripts/idol-video.py \
  --ref-image "https://platform-outputs.agnes-ai.space/images/t2i/820dd08f8ab24c47a23770d028a9a691.png" \
  --scenes-file references/pink-panther-prompts.json \
  --scenes 5 --duration 5
```

## 參數

| 參數 | 值 | 說明 |
|---|---|---|
| model | agnes-video-v2.0 | — |
| image | 參考圖 URL | 所有場景共用 |
| num_frames | 113 | 5 秒 × 24fps = 120 → 8n+1 = 121 → 限制後 113 |
| frame_rate | 24 | — |
| negative_prompt | (完整角色保留詞群) | 自動由 idol-video.py 加入 |
| 輸出解析度 | 1088×832 | 依輸入圖片比例自動決定 |
