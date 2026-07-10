---
name: img2vid-character
description: 圖生影角色一致性提示詞架構 — 讓影片中的角色不跑掉
version: 1.0.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [video, prompt, character, consistency, img2vid]
    related_skills: [agnes-prompt-architect, idol-video-pipeline, agnes-quota-router]
status: stable
---

# 🎯 圖生影角色一致性 (img2vid-character)

## 觸發條件

圖生影任務中需要保持角色/主體不變，或上一輪生成的角色跑掉時。

## 問題

Agnes Video V2.0 的 `ti2vid` 模式（圖+文→影）會以輸入圖片為參考，但**角色外觀經常在動畫過程中漂移** — 髮型變了、五官變了、甚至變成另一個人。

## 三層 Prompt 結構

這是與一般影片提示詞最大的不同處 — 一般影片 prompt 只要描述「要什麼」，圖生影還需要描述「什麼不動」。

```
┌─ Layer 1: 保留層 (Preserve) ────── 定義哪些特徵必須完全一致
│   放在 prompt 結尾或開頭
│   範例: "keeping face, hairstyle, outfit, and body proportions 
│           identical to the reference image throughout the entire video"
│
├─ Layer 2: 動態層 (Animate) ─────── 定義「最小必要 motion」
│   只描述一定要動的部分，越少越好
│   範例: "hair gently swaying, subtle breathing motion, 
│           microphone slowly lowering"
│
└─ Layer 3: 場景層 (Scene) ───────── 背景/燈光/運鏡
    範例: "stage lights slowly changing from blue to warm amber,
            soft fog drifting across stage, camera slowly dolly in"
```

### Motion 越少越好

| Motion 量 | 角色保留成功率 | 適用場景 |
|:---------|:-------------|:---------|
| 🟢 **微動**（頭髮飄、呼吸、微笑） | 高 | 特寫、深情歌唱 |
| 🟡 **中動**（走路、舉手、轉身） | 中 | 舞台走位、舞蹈靜態 pose |
| 🔴 **大動**（跳舞、跑、跳、旋轉） | 低 | 不建議用 ti2vid，改用關鍵幀 |

## 負面提示詞（必填）

### 角色保留詞群（核心）

```
different character, face change, identity change, face morphing,
different hairstyle, different outfit, appearance drift, 
character mutation, swapped identity, face distortion,
inconsistent appearance, face melting, feature blending,
different person, losing character identity
```

### 品質詞群（通用）

```
ugly, deformed, bad anatomy, blurry, jittery, distorted,
low quality, bad quality, worst quality, watermark, text,
subtitles, artifacts
```

### 完整負面提示詞（可直接複製）

```
different character, face change, identity change, face morphing,
different hairstyle, different outfit, appearance drift,
character mutation, swapped identity, face distortion,
inconsistent appearance, ugly, deformed, bad anatomy,
blurry, jittery, distorted, low quality
```

## 圖生影 Prompt 模板

### 模板結構
```
[場景描述], [保留角色特徵完全一致], [最小必要 motion]
```

### 實例對照

| 場景 | 一般 prompt（會跑掉） | ✅ 修正版（角色保留） |
|:----|:-------------------|:-------------------|
| 主歌特寫 | Close-up of idol singing, eyes closed, warm lighting | Close-up of idol singing into microphone, **keeping face, hair and outfit identical to reference**, eyes slowly closing with emotion, subtle smile, warm amber backlight, bokeh background |
| 舞蹈中景 | Idol dancing on stage, colorful lights, confetti | Idol **keeping exact same character appearance**, dancing energetically on stage, hair naturally flowing with motion, colorful stage lights, confetti falling, happy expression |
| 結尾鞠躬 | Idol bowing to audience, golden lighting, finale | Idol **with face and outfit unchanged from reference**, bowing to audience with grateful smile, golden warm lighting, confetti settling |

## 技術注意事項

### 影片 API 參數

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "[場景+保留+動態三層結構]",
  "image": "https://...public-image-url...",
  "negative_prompt": "different character, face change, ... (完整角色保留詞群)",
  "num_frames": 121,
  "frame_rate": 24,
  "width": 576,
  "height": 1024
}
```

### 關鍵陷阱

| 陷阱 | 說明 |
|:----|:------|
| ❌ **`image` 不接受 Base64** | 圖生影的 `image` 參數是**單一字串**，必須是公開 URL。圖生圖的 `extra_body.image` 是陣列，可接受 Base64 Data URI。兩者完全不同 |
| ❌ **不要用 `remixed_from_video_id`** | 輪詢回應中影片連結在 **`url`** 欄位。`remixed_from_video_id` 常為 null |
| ✅ **固定 seed** | 設定固定 `seed` 參數可讓同一場景的多次生成結果更穩定 |
| ✅ **比例鎖死** | width/height 要與輸入圖片比例一致，否則 API 會自動 normalize 導致裁切 |
| ⚠️ **8n+1 幀數規則** | `num_frames` 必須符合 `8n + 1`（如 81, 89, 97, ..., 441） |

### 幀數-時長對照 (@24fps)

| 目標時長 | num_frames | 適合 |
|:--------|:----------|:------|
| ~3 秒 | 81 | 短循環 |
| ~5 秒 | 121 | 標準場景 |
| ~10 秒 | 241 | 長場景 |
| ~18 秒 | 441 | 上限 |

## 與一般影片提示詞的差異

| 面向 | 一般文生影 | 圖生影（角色保留） |
|:----|:----------|:----------------|
| 主體描述 | 自由創作角色 | **保留輸入圖片的角色** |
| Motion | 越多越好 | **越少越好** |
| 負面提示詞 | 品質詞即可 | **角色保留詞 + 品質詞** |
| 失敗模式 | 不自然 | **角色跑掉**（更難修） |

## 實測記錄

| 項目 | 結果 |
|:----|:------|
| 文生圖作參考 → 圖生影 | ✅ 角色尚可，但 img2img 預處理會改動角色 ❌ |
| 原圖直接圖生影 | ✅ 角色保留較好 |
| 無負面提示詞 | ❌ 角色漂移嚴重 |
| 有角色保留負面詞 | ✅ 穩定性明顯提升 |
| 5 秒場景 (121 frames) | ✅ 角色保留 ~3-4 秒後開始微漂，但可接受 |
| 大型運動（跳舞） | ⚠️ 角色漂移風險高，建議微動 |

## 參考資源

- `agnes-prompt-architect` — 通用提示詞架構（10 維度影片版）
- `idol-video-pipeline` — 四階段影片製作工作流
- `agnes-quota-router/references/agnes-video-v2.0.md` — Video API 參考
- `references/api-response-reference.md` — 實測 API 回應結構（欄位對照、比例 normalize、錯誤碼）
