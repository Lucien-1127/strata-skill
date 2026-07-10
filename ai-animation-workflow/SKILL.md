---
name: ai-animation-workflow
description: "圖片鎖定構圖/風格；影片提示詞只描述動態。含角色一致性。"
version: 4.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [Animation, I2V, Prompt, Video, Character-Consistency]
status: stable
---

# AI 動畫工作流 v4.1 — 圖片先行的 I2V 流程 + 角色一致性

> 核心原則：圖片鎖定視覺品質，影片提示詞只描述「什麼在動」

## 分工原則

| 角色 | 負責 | 不負責 |
|------|------|--------|
| **圖片** | 構圖、主體、光影、風格、材質 | 動態描述 |
| **影片提示詞** | 什麼在動、怎麼動、鏡頭運動、時間順序 | 描述圖片已有的東西 |

## 三層 Prompt 結構（img2vid-character 整合）

圖生影與文生影最大的不同 — 圖生影需要告訴 AI「什麼不要動」：

```
Layer 1: 保留層 (Preserve)    → "keeping face, body, color identical to reference"
Layer 2: 動態層 (Animate)     → "hair swaying, subtle breathing, tail curling" (越少越好)
Layer 3: 場景層 (Scene)       → "warm lighting, simple background, camera dolly in"
```

### Motion 越少越好

| Motion 量 | 角色保留成功率 |
|:---------|:-------------|
| 🟢 微動（頭髮飄、呼吸、眨眼） | 高 |
| 🟡 中動（走路、轉身、舉手） | 中 |
| 🔴 大動（跑、跳、跳舞） | 低 |

## 步驟一：設計「可動的圖片」

圖片需要為後續動畫預留空間：
- 主體姿勢自然可動
- 背景有深度層次
- 畫面中埋入「暗示動態」的元素
- 留邊讓運鏡有空間

### 圖片提示詞公式（Agnes Image 2.1 Flash）
```
[主體] in [場景], [姿勢], cinematic composition, [光線], [風格],
clean sharp details, no motion blur, well-lit
```

## 步驟二：I2V 影片提示詞

### 圖生影完整模板
```
keeping [角色特徵] identical to the reference image throughout the entire video,
[最小必要 motion], [環境動態], [鏡頭運動]
```

### 角色保留負面提示詞（必填，完整版）
```
different character, face change, identity change, face morphing,
different body shape, different color, appearance drift,
character mutation, swapped identity, face distortion,
inconsistent appearance, ugly, deformed, bad anatomy, blurry, jittery, distorted
```

## 步驟三：多場景角色一致性

同一個角色在多個場景出現時，**不要靠文字維持角色**：

1. **先產一張角色參考圖**（標準姿勢、純色背景、無動態模糊）
2. **所有場景共用同一張參考圖**作為圖生影的起始幀
3. 每場景 prompt 開頭都加「keeping face, body, color identical to reference」
4. 所有場景加上相同的角色保留負面提示詞
5. 串接時用 crossfade 淡出淡入

## 步驟四：Frame Chaining（進階串接）

用前一鏡頭的最後一格作為下一鏡頭的起始圖片，達到無縫銜接：

```
Clip 1 (5s): 參考圖A → 圖生影 → 產出影片A
                    ↓ 取最後一幀
Clip 2 (5s): 影片A末幀 → 圖生影 → 產出影片B → 兩段無縫
```

## 實戰案例：頑皮豹 25 秒動畫（2026-07-08）

**第一次（失敗）：** 每場景獨立文生圖 → 頑皮豹長相每場都不一樣 → 用戶說「不連貫、完全看不懂」

**修正後（成功）：** 共用同一張參考圖 + 角色保留負面詞 + `keeping features identical to reference` + crossfade

### 關鍵教訓（納入流程）
- ❌ 不要靠文字 prompt 維持角色一致性 — 每次文生圖都會發明新版本
- ✅ 同一個參考圖餵給所有場景，角色才不會跑掉
- ✅ 「keeping ... identical to reference」放在影片 prompt 開頭
- ✅ 角色保留負面提示詞是必填，不是選填
- ✅ crossfade 串接比硬切流暢
- ⚠️ 動畫角色（非真人）的輪廓穩定性較高，但顏色仍會漂移

### 場景腳本範例（角色保留版）
```json
{
  "title": "開場 — 經典踱步",
  "prompt": "keeping face, body shape, pink color, tail, and white gloves identical to the reference image, character slowly walking forward with cool confident swagger, shoulders gently swaying, minimalist white background"
}
```

## 步驟五：角色一致性方案優先級

從實戰與產業研究中得出的角色一致性方案排名（從最有效到最不可靠）：

| 排名 | 方案 | 一致性 | 靈活性 | 成本 | 適用場景 |
|:----|:-----|:-------|:-------|:-----|:---------|
| 🥇 | **共用參考圖 + I2V** | 🟢 高 | 🟢 高 | 🟢 低 | 多場景同一角色，最簡方案 |
| 🥈 | **IP-Adapter + AnimateDiff** | 🟢 高 | 🟡 中 | 🟡 中 | 風格/角色雙重保持一致 |
| 🥉 | **Face Swap 後製（FaceFusion/ReActor）** | 🟢 高 | 🟡 中 | 🟢 低 | 真人臉部替換補救 |
| 4 | **ControlNet (OpenPose/Canny/Depth)** | 🟢 高 | 🔴 低 | 🟡 中 | 特定姿態/構圖控制 |
| 5 | **Frame Chaining（末幀→起始）** | 🟢 高 | 🟡 中 | 🔴 高 | 長鏡頭連續場景 |
| ❌ | **純文字 prompt 描述角色** | 🔴 低 | 🟢 高 | 🟢 低 | **不要用** — 每次文生圖都會發明新版本 |

**關鍵原則**：共用參考圖 > IP-Adapter > Face Swap > ControlNet > 文字 prompt

### Motion 量 vs 角色保留成功率（完整版）

| Motion 量 | 角色保留成功率 | 建議處理方式 |
|:---------|:-------------|:------------|
| 🟢 微動（頭髮飄、呼吸、眨眼） | 高 (80-95%) | 標準 I2V 即可 |
| 🟡 中動（走路、轉身、舉手） | 中 (50-70%) | 加 IP-Adapter + ControlNet 雙重約束 |
| 🔴 大動（跑、跳、跳舞） | 低 (20-40%) | Face Swap 後製補救 + 多段重試篩選 |

## 步驟六：60 秒以上長片製作

### 現有方案比較

| 方法 | 極限時長 | 技術複雜度 | 品質 | 成本 |
|:----|:---------|:----------|:-----|:-----|
| **多場景串接 + Crossfade**（主流） | 理論無限 | 🟡 中 | 🟢 高 | 🟡 中 |
| **LTX Studio 自迴歸** | ~60 秒 | 🟢 低 | 🟡 中 | 🟡 中 |
| **Frame Chaining（逐幀連接）** | 理論無限 | 🔴 高 | 🟢 非常高 | 🔴 高 |
| **AnimateDiff 長序列** | ~8 秒/批次 | 🔴 高 | 🟡 中 | 🟡 中 |
| **專業商業方案**（Runway/Pika） | 取決於帳戶方案 | 🟢 低 | 🟢 高 | 🔴 高 |

### 實戰步驟（60 秒動畫）

```
Step 1: 規劃 12-15 張關鍵圖片（不同場景/角度）
Step 2: 每場景獨立 I2V（共用參考圖 + 角色保留 negative prompt）
Step 3: 檢查每段影片品質（ffprobe 確認 size > 0, 解析度一致）
Step 4: ffmpeg concat 串接 + crossfade 轉場
Step 5: 配樂配音（ElevenLabs / Suno / Runway Add Dialogue）
Step 6: 最終渲染輸出
```

### 素材需求

| 模式 | 圖片需求 | 適用工具 |
|:----|:---------|:---------|
| AI 延伸生成（主流） | **12-15 張**核心圖片 | Agnes Video, Runway, Pika, Kling, AnimateDiff |
| 逐幀 AI 動畫（流體） | **720-1,440 張**（12-24 FPS） | Deforum, AnimateDiff, ComfyUI |

## 步驟七：業界工具鏈生態

### 常用模型矩陣

| 模型/平台 | 類型 | 開源? | 主要用途 | 特色 |
|:---------|:-----|:------|:---------|:-----|
| **Stable Diffusion** 1.5/XL | 文生圖 | ✅ 開源 | 圖片生成基底 | HuggingFace 最多社群 |
| **FLUX** (Black Forest Labs) | 文生圖 | ✅ 開源 | 高品質圖片 | Pro+Dev+Schnell 三版本 |
| **AnimateDiff** | 圖生影 | ✅ 開源 | 動畫生成 | 插入式，無需訓練 |
| **ComfyUI** | 工作流引擎 | ✅ 開源 | 節點式生產線 | 120K⭐ GitHub |
| **Runway Gen-4.5** | 文生影 | ❌ 閉源 | 專業影片 | 5000 萬用戶 |
| **LTX-2** (Lightricks) | 文生影 | ✅ 開源 | 近即時生成 | 13B 參數 |
| **Wan 2.1** (Alibaba) | 文生影 | ✅ 開源 | 高效生成 | 開源替代方案 |
| **Pika** | 文生影 | ❌ 閉源 | 短影片 | 易用界面 |
| **Kling 3.0** (Kuaishou) | 文生影 | ❌ 閉源 | 中國市場 | 高品質 |
| **Veo 3.1** (Google) | 文生影 | ❌ 閉源 | 高品質 | 整合 LTX Studio |

### 後製工具鏈

| 類別 | 工具 | 用途 |
|:----|:-----|:-----|
| **影片編輯** | Premiere Pro、DaVinci Resolve、CapCut | 剪輯、調色、轉場、字幕 |
| **特效合成** | After Effects、Runway Aleph 2.0 | 合成、光效、動態圖形 |
| **語音/音效** | ElevenLabs、Runway Add Dialogue、Suno | TTS 旁白、配音、音樂生成 |
| **唇形同步** | Runway Add Dialogue、Flawless DeepEditor | 對話自動對嘴 |
| **串接** | ffmpeg concat demuxer、Premiere Pro | 多片段串接 |
| **臉部處理** | FaceFusion (29K⭐)、ReActor、Roop | 臉部替換/一致性補救 |

## 注意事項
- Agnes Video V2.0 的 `image` 參數只接受公開 URL（不接受 Base64 Data URI）
- 幀數必須符合 8n+1 規則（81, 89, 97, ..., 441）
- 輪詢 `/agnesapi` 的回應中影片 URL 在 `url` 欄位（非 `remixed_from_video_id`）
- idol-video.py 已內建角色保留負面提示詞
- **閉源 API 依賴風險高**（Sora 2026-04-26 關閉、API 2026-09 終止）— 關鍵項目需有備援方案
- **解析度不一致**會導致 ffmpeg 串接失敗 — 用 ffprobe 檢查後統一縮放

## 參考
- `img2vid-character` — 圖生影角色一致性提示詞架構（三層結構 + 負面詞模板）
- `media-pipeline` — FEG 流水線（支援 idol 模式 + crossfade）
- `idol-video-pipeline` — 四階段角色影片工作流
- `references/animation-production-guide.md` — 60 秒動畫素材需求評估
- `references/ai-animation-industry-research.md` — 2026 年 AI 動畫產業深度研究（工作室/工具鏈/市場/痛點）
- `references/western-ai-video-api-reference.md` — 歐美影片生成 API 定價與規格（Runway/Pika/Luma/Sora/Stability）
- `references/asia-ai-video-platforms-reference.md` — 中國/亞洲 AI 影片平台對比（Kling/Vidu/CogVideo/Wan/Jimeng）含台灣適用評估
