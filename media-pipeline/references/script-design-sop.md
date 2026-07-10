# 腳本設計 SOP — 5 步驟 + Coherence Pass

> 在進入 AI 圖片生成與影片製作之前，腳本設計是決定成品品質的關鍵環節。
> 通用方法論，不綁定特定 pipeline 腳本 — 適用於 pipeline-feg.py、CineAgent run_pipeline.py、或任何自訂流水線。

---

## 核心流程

```
Step 1: 需求萃取
    │
Step 2: 節奏表 (Beat Sheet)         溫度 0.3
    │
Step 3+4: 腳本撰寫 + 分鏡設計       溫度 0.7
    │
Step 5: Coherence Pass               溫度 0.1
    │
最終: 腳本審查
```

---

## Step 1 — 需求萃取

從用戶輸入萃取關鍵要素：

| 要素 | 範例 |
|:----|:----|
| 主題核心 | 霓虹城市雨夜，賽博龐克氛圍 |
| 目標平台 | shorts / reels / tiktok / youtube |
| 格式比例 | 9:16（預設）/ 16:9 / 1:1 |
| 總時長 | 15s / 30s / 60s |
| 視覺風格 | 寫實 / 動畫 / 賽博龐克 / 奇幻 |
| 情緒調性 | 神秘 / 動感 / 沉思 / 寧靜 |
| 特殊要求 | 角色一致性 / 產品展示 |

**輸出**: 萃取的參數清單（傳遞給 Step 2）。

---

## Step 2 — 節奏表 (Beat Sheet)

**Temperature: 0.3** — 低溫確保 JSON 結構穩定。

將總時長分配為多個「節拍」(beats)，每個 beat 定義：

```json
{
  "beat_id": 1,
  "name": "Hook",
  "time_start": 0, "time_end": 3,
  "purpose": "吸引眼球",
  "emotion": "好奇",
  "camera": "特寫"
}
```

### 平台對應節奏模板

| 時長 | 結構 | 場景數建議 |
|:---:|:----|:---------:|
| **15s** | Hook(0-3) → 核心展示(3-10) → 反轉(10-13) → 收尾(13-15) | 2-3 |
| **30s** | Hook(0-3) → Setup(3-8) → 衝突(8-15) → 高潮(15-25) → Outro(25-30) | 3-5 |
| **60s** | Hook(0-5) → 情境(5-15) → 情感(15-25) → 衝突(25-35) → 解決(35-45) → 高潮(45-55) → CTA(55-60) | 5-7 |
| **3min** | 第一幕(25%) → 第二幕(50%) → 第三幕(25%) | 7-12 |

### 情緒曲線

設計整支影片的情緒起伏，常見曲線：

- **引入→上升→高潮→收束**（標準短影片）
- **平靜→緊張→爆發→餘韻**（故事型）
- **好奇→興趣→驚嘆→滿足**（展示型）

**輸出**: 完整 beat_sheet JSON，含 beats 陣列 + emotion_curve。

---

## Step 3+4 — 腳本撰寫 + 分鏡設計（合併執行）

**Temperature: 0.7** — 中溫保留創造力。

將節奏表轉化為逐場景分鏡。每場景包含以下欄位：

```json
{
  "scene_id": 0,
  "scene_title": "序幕 — 雨中霓虹天際線",
  "scene_goal": "展示未來都市雨夜景觀",

  "visual_style": "所有場景必須完全相同（同一世界觀）",
  "character_card": "所有場景必須逐字相同（角色連貫性的鎖定依據）",

  "image_prompt": "只描述靜態畫面：主體/場景/光線/風格/材質。不含動態。",
  "image_negative_prompt": "過濾低品質與解剖錯誤",

  "video_prompt": "只描述動態：主體動作/環境動態/鏡頭運動。不重複靜態元素。",
  "video_negative_prompt": "過濾閃爍/形變/不連貫",

  "transition_rule": "dissolve/cut/wipe/morph",
  "duration_seconds": 5,
  "beat_order": 1,
  "emotion": "神秘",
  "camera_angle": "低角度/平視/俯視/跟拍",
  "width": 768,
  "height": 1152
}
```

### Image / Video Prompt 分離原則（⛔ 鐵律）

| 層 | 描述什麼 | 不能描述什麼 |
|:--|:---------|:------------|
| **image_prompt** | 主體外觀、場景佈置、光線方向、材質紋理、色彩風格 | ❌ 主體動作、鏡頭運動、動態粒子 |
| **video_prompt** | 主體做什麼動作、鏡頭如何移動、環境動態（雨/煙/粒子） | ❌ 重複主體長相、場景細節、光線描述 |

**為什麼重要**：Agnes Video 2.0 的 I2V 模式以圖片為主體資訊來源，video_prompt 中的靜態描述會與圖片衝突，導致角色漂移。

### 負面提示詞模板

```text
# Image 負面（通用）
worst quality, low quality, blurry, bad anatomy, extra fingers,
missing limbs, deformed, ugly, cartoon, 3d render, cgi, watermark,
text, logo, overexposed, underexposed

# Video 負面（通用）
blurry, flickering, inconsistent character, morphing face,
jump cut, teleportation, color shift, frame duplication,
cartoon, cgi, watermark, text
```

### 腳本撰寫原則

| 原則 | 說明 |
|:----|:-----|
| **視覺化寫作** | 用畫面思考，非文字思考 |
| **精簡** | 每場景一句話描述核心 |
| **可視性** | 確認每個描述都能被 AI 模型理解 |
| **連續性** | 前後場景視覺元素一致 |
| **節奏感** | 長短場景交錯，避免單調 |
| **可動性** | 圖片中的主體姿勢要是「可以動的」（非誇張靜態 pose） |

**輸出**: 分鏡 scene JSON 陣列。

---

## Step 5 — Coherence Pass（一致性審查）

**Temperature: 0.1** — 極低溫，嚴格審查不創造。

在腳本生成完成後執行，確保跨場景角色/風格一致：

1. 收集所有場景的 `{scene_id, character_card, visual_style}`
2. 送 LLM 比對差異
3. LLM 輸出統一版本（所有不一致的欄位被修正為同一值）
4. 若 LLM 失敗，跳過不中斷流程

**審查項目**：

```text
□ 連續性檢查
   □ character_card 跨場景完全相同
   □ visual_style 跨場景完全相同
   □ 場景方向感一致（左右/前後不矛盾）
   □ 光線/色調延續合理
   □ 情緒曲線有邏輯
   □ 轉場方式符合內容調性

□ 負面提示詞檢查
   □ 每場景都有 image_negative_prompt
   □ 每場景都有 video_negative_prompt
   □ 負面詞涵蓋品質/一致性/風格偏移

□ prompt 分離檢查
   □ image_prompt 不包含動態描述
   □ video_prompt 不重複靜態內容
   □ duration_seconds 在 5-15s 範圍內
   □ 總時長符合目標平台規範
```

**輸出**: 修正後的 scene JSON 陣列 + review_notes。

---

## 最終輸出結構

```json
{
  "run_id": "a1b2c3d4",
  "theme": "主題描述",
  "platform": "shorts",
  "total_duration_target": 30,
  "emotion_curve": "平靜→緊張→高潮→收束",
  "total_scenes": 5,
  "beats": [...],
  "scenes": [...],
  "review_notes": [
    "總時長: 25s (5 場景)",
    "✅ character_card 跨場景一致"
  ]
}
```

---

## 與 pipeline-feg.py 的整合

pipeline-feg.py 目前不包含腳本設計階段（Step 0 僅載入 JSON）。要使用本 SOP：

1. **手動流程**：依本指南建立場景 JSON → `--scenes-file /tmp/scenes.json` 載入
2. **半自動流程**：用 CineAgent（`~/CineAgent/run_pipeline.py`）執行 Phase 0 生成腳本 → 輸出 scene_prompts.json → 若需用 pipeline-feg.py 跑，轉換格式後載入
3. **全自動流程**：改跑 CineAgent `run_pipeline.py --topic "主題"`（內建完整 5 步驟）

## 參考連結

- `參考資料:references/beat-sheet-templates.md` — 更多節奏模板
- `CineAgent-v3.2.md` — CineAgent 實作（內建完整腳本 SOP）
- `neon-rain-cinematic-scenes.json` — 應用範例：5 場景霓虹城市雨夜
- `references/video-api-pitfalls.md` — 影片 API 常見陷阱
