---
name: agnes-prompt-architect
description: Unified prompt architecture for Agnes image + video generation
version: 1.0.0
author: Hermes
metadata:
  hermes:
    tags: [Agnes, Prompt, Image, Video, Generation]
platforms: [linux]
---

# Agnes Prompt Architect

統一的提示詞架構系統，覆蓋 **Agnes Image 2.1 Flash**（文生圖/圖生圖）與 **Agnes Video V2.0**（文生影/圖生影/多圖/關鍵幀）。支援快速模式與對話精修模式雙路由，使用 8 維度框架（圖片）和延伸維度（影片）。

## When to Use

- "幫我想一個圖片提示詞"
- "生成一張圖，主題是..."
- "我想要一個影片提示詞"
- "把這張圖做成動畫"
- "幫我設計一個產品圖的 prompt"
- "我想做一段影片，內容是..."

## Prerequisites

- Agnes API key 在 `~/.hermes/env/agnes.env`（由 agnes-quota-router 管理）
- `agnes-quota-router` 技能 — 處理路由與 API 端點
- `agnes-quota-router/references/agnes-image-2.1-flash.md` — Image API 參考
- `agnes-quota-router/references/agnes-video-v2.0.md` — Video API 參考

## How to Run

輸入自然語言描述想法 → 技能自動分類（圖片/影片）→ 進入對應流程：
- **快速模式**：直接輸出 2-3 組完整提示詞草稿
- **對話精修模式**：逐步收斂 8 維度

---

## 核心架構

### 任務分類（第一道路由）

```
輸入
  │
  ├─ 涉及「動態/運動/時間/鏡頭移動」─→ 影片提示詞流程
  │    關鍵詞: 走/跑/飛/旋轉/轉場/從A到B/慢動作/縮時
  │
  └─ 靜態畫面 ─→ 圖片提示詞流程
       沒有時間/運動維度的描述
```

### 雙模式（與圖片指南共用）

```
快速模式：直接輸出 2-3 組多版本草稿
對話精修模式：逐步引導補齊維度
```

---

## 圖片提示詞架構（8 維度）

| # | 維度 | 說明 | 範例 |
|:-:|:-----|:-----|:------|
| 1 | **主體** | 核心對象、動作、表情、數量 | 一隻橘貓蹲在木椅上 |
| 2 | **媒介** | 材質或工具 | 油畫、3D渲染、水彩、攝影 |
| 3 | **風格** | 藝術運動或視覺語言 | 賽博龐克、吉卜力、寫實、浮世繪 |
| 4 | **光影** | 光源、方向、情緒 | 日落背光、柔光箱、霓虹、燭光 |
| 5 | **色彩** | 色調、飽和度、色溫 | 暖橙調、冷藍、高飽和、復古褪色 |
| 6 | **構圖** | 角度、取景、佈局 | 鳥瞰、居中、三分法、引導線 |
| 7 | **攝影參數** | 鏡頭、光圈、景深 | 廣角、f/1.8 淺景深、長焦壓縮 |
| 8 | **渲染品質** | 解析度、細節層級 | 8K、超精細、照片級寫實 |

### 推薦提示詞結構

```
[主體] + [場景/環境] + [風格] + [光照] + [構圖] + [品質]
```

### 輸出格式（圖片）

```json
{
  "type": "image",
  "model": "agnes-image-2.1-flash",
  "prompt": "完整8維度提示詞",
  "size": "1024x768",
  "extra_body": {"response_format": "url"}
}
```

---

## 影片提示詞架構（8+2 延伸維度）

影片與圖片共享前 4 維（主體、媒介、風格、光影），但需延伸 6 個時空維度：

| # | 維度 | 說明 | 與圖片差異 |
|:-:|:-----|:-----|:----------|
| 1 | **主體 + 動作** | 核心對象及其運動軌跡 | **非靜態**，需描述動作方向與速度 |
| 2 | **媒介** | 實拍/CGI/動畫 | 同圖片 |
| 3 | **風格** | 藝術運動或視覺語言 | 同圖片 |
| 4 | **光影** | 光源隨時間變化 | 可動態變化（如：夕陽→夜晚轉場） |
| 5 | **色彩** | 色調、飽和度、色溫 | 可隨時間漸變 |
| 6 | **構圖 + 鏡頭運動** | 取景 + 相機運動方式 | **★ 新增：鏡頭運動**（推/拉/搖/移/跟/升降） |
| 7 | **時間與節奏** | 時長、速度、節奏感 | **★ 新增：純時間維度** |
| 8 | **場景動態** | 背景元素的運動層次 | **★ 新增：多層運動**（前景/中景/背景） |
| 9 | **圖生影保留範圍** | 圖生影時要保留什麼 | 同圖生圖的「保留構圖」 |
| 10 | **關鍵幀控制** | 多圖過渡或關鍵幀動畫 | 僅關鍵幀模式需要 |

### 鏡頭運動詞彙表

| 運動 | 效果 | 範例提示詞 |
|:-----|:-----|:-----------|
| **推 (Dolly in)** | 鏡頭慢慢靠近主體 | "slow dolly in toward the subject" |
| **拉 (Dolly out)** | 鏡頭慢慢遠離主體 | "gradual dolly out revealing the scene" |
| **搖 (Pan)** | 水平轉動鏡頭 | "panning left across the landscape" |
| **移 (Truck)** | 鏡頭平行移動 | "trucking shot following the character" |
| **跟 (Follow)** | 跟隨主體運動 | "following shot tracking the runner" |
| **升降 (Boom)** | 鏡頭垂直移動 | "booming up from ground to rooftop" |
| **手持 (Handheld)** | 抖動的真實感 | "cinematic handheld camera, slight shake" |
| **固定 (Static)** | 鏡頭固定，主體運動 | "static wide shot, subject walks through frame" |
| **縮時 (Timelapse)** | 長時間壓縮 | "timelapse of clouds moving across sky" |
| **慢動作 (Slow-mo)** | 動作放慢 | "slow motion water splash, every droplet visible" |

### 時間節奏控制

| 節奏 | 適用場景 | 參數建議 |
|:-----|:---------|:---------|
| **平穩 (Calm)** | 風景、氛圍片 | frame_rate=24, 慢速運動 |
| **動態 (Dynamic)** | 動作、運動 | frame_rate=30, 快速剪輯感 |
| **戲劇 (Dramatic)** | 慢動作高潮 | frame_rate=24, slow-mo 描述 |
| **縮時 (Timelapse)** | 日夜轉換 | frame_rate=24, 長時間壓縮描述 |

### 常用時長-幀數對照

| 目標時長 | num_frames @24fps | 適用場景 |
|:--------|:-----------------|:---------|
| ~3 秒 | 81 | 短循環、產品展示 |
| ~5 秒 | 121 | 社交短片、Reels |
| ~10 秒 | 241 | 標準片段、場景展示 |
| ~18 秒 | 441 | 完整場景、敘事片段 |

### 輸出格式（影片）

```json
{
  "type": "video",
  "model": "agnes-video-v2.0",
  "prompt": "完整10維度提示詞",
  "num_frames": 121,
  "frame_rate": 24
}
```

圖生影額外提供 `image`（單字串，公開 URL）。
多圖/關鍵幀使用 `extra_body.image`（陣列）和 `extra_body.mode`。

---

## 圖生圖/圖生影專用規則

**固定模板結構**，適用於所有基於輸入圖片的生成：

```
Transform {要改的內容} while preserving {要保留的內容}
```

| 模式 | 輸入 | 說明 |
|:-----|:-----|:------|
| **圖生圖** | extra_body.image（陣列） | 可接受 URL 或 Data URI Base64 |
| **圖生影** | image（單字串） | **只接受公開 URL**，不接受 Base64 |
| **多圖影片** | extra_body.image（陣列） | 多張參考圖 |
| **關鍵幀** | extra_body.image + mode="keyframes" | 過渡動畫 |

### 圖生影 Pipeline（已實測）

```
文生圖 → platform-outputs URL
       → POST /v1/videos image=該URL
       → 輪詢 /agnesapi?video_id=<ID>
       → result.remixed_from_video_id
```

---

## 流程規則

### 狀態機（圖片與影片共用）

| 狀態 | 條件 | 行為 |
|:----|:-----|:-----|
| **A** | 已知維度 < 5 | 每輪處理 ≤2 維度，含 1 個錨點 |
| **B** | 已知維度 ≥ 5 | 詢問準備好產出抑或補充細節 |
| **C** | 使用者要求直接輸出 | 立即輸出完整提示矩陣 |

### 錨點設計（每輪必須有一個）

| 場景 | 錨定維度 |
|:-----|:---------|
| 情感/氛圍抽象 | 媒介 或 風格 |
| 主體未知 | 主體 |
| 影片、運動為主 | 主體+動作 或 鏡頭運動 |
| 風格與媒介皆未知 | 對提示詞方向影響較大的維度 |

### 快速模式路由

- 使用者要求快速模式 → 跳過維度引導，直接輸出 2-3 組草稿
- 每組草稿需不同視角/構圖/風格方向
- 完整包含所有維度，未知項以佔位符標示
- 使用者選中後可進入精修微調

### 對話精修模式規則

- 預設模式（未指定時）
- 每輪最多處理 2 維度，其中包含 1 個錨點
- 所有猜測值需使用者確認才算已知
- 每輪回應必須輸出當前累積草稿（含所有維度，未填者佔位符）

---

## 自我檢查清單

1. 確認分類：圖片還是影片？
2. 確認當前狀態：A/B/C
3. 確認本輪有一個明確錨點維度（除非狀態 C）
4. 確認草稿包含全部維度（圖片8/影片10），未填者佔位符
5. 表情符號 ≤2，只用 ✨🎨🤔💡✅🎉🚀📋
6. 圖生圖/影確保「保留什麼」與「改什麼」都寫清楚
7. 最終輸出無佔位符

## Pitfalls

- **影片不等於圖片加動態**：影片需要時間維度的設計（鏡頭運動、節奏、場景動態），不是把圖片 prompt 加上 "in motion" 就夠
- **圖生影不接受 Base64**：image 參數必須是公開 URL，這點與圖生圖完全不同
- **response_format 不可放頂層**：永遠放在 extra_body 內
- **圖生圖不需要 tags: ["img2img"]**
- **錨點不要跳躍**：每輪只能有一個主要錨點，不要同時追問多個不相關維度
- **影片幀數限制**：num_frames ≤ 441 且必須 8n+1

## Verification

```bash
# 驗證圖片提示詞
python3 -c "
prompt='A red apple on white background, product photography, soft studio lighting'
# 確認包含主體、場景、風格要素
assert len(prompt) > 30, 'Prompt too short'
print('✅ Prompt valid')
"

# 驗證影片提示詞包含運動描述
python3 -c "
prompt='A cat walking across the frame, slow dolly in, sunset lighting'
assert any(w in prompt.lower() for w in ['walk','run','fly','move','pan','dolly','follow']), 'Missing motion'
print('✅ Video prompt includes motion')
"
```

## References

- `agnes-quota-router/references/agnes-image-2.1-flash.md` — Image API 細節
- `agnes-quota-router/references/agnes-video-v2.0.md` — Video API 細節
- `agnes-quota-router/SKILL.md` — 路由與金鑰管理
- `media-pipeline/SKILL.md` — 自動化流水線執行引擎
- `media-pipeline/scripts/pipeline.py` — Python 執行腳本（金鑰從 env 讀取，不在 repo 內）
