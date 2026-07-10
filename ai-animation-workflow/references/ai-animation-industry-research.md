# AI 動畫產業生產 Pipeline 深度研究（2026-07-09）

> 爬取來源：Wikipedia API、GitHub API、Reddit PullPush API、HN Algolia API、Variety、Runway 產品頁

## 知名工作室

| 工作室 | 重點 | 技術路線 |
|:-------|:-----|:---------|
| **Fable Studio** | 2018 創立，VR + "The Simulation" + SHOW-1 (AI Showrunner) 自動產製 South Park 集數；2019 艾美獎 | 多 LLM Agent 協作敘事 + 生圖模型 |
| **Spiridellis Bros. Studios** | JibJab/StoryBots 創辦人，獲 Google AI Futures Fund + Ashton Kutcher 投資，2025.10 成立，首作 2026.01 | AI 自製原創 IP，跨平台資產 |
| **Runway** | 5000 萬用戶，Gen-4.5, Characters (即時AI Agent), Multi-Shot, Aleph 2.0, GWM-1, AI Film Festival | 全端影片生態系 + 開源研究 |
| **LTX Studio (Lightricks)** | 2024.02 推出，故事板式製作，LTX-2 開源，自迴歸~60秒，整合 Veo 3 | 近即時生成，開源模型策略 |
| **Pika Labs** | 美國 AI 影片平台 | 簡潔介面 |
| **Kling AI** | Kuaishou 旗下，中國 AI 創意工作室 | 高品質競爭 |
| **Benten Film** | 原名 Gaina，2025.08 被 Creator's X 收購 | 日本 AI 動畫 |
| **Amazon AI 動畫計畫** | Jorge Gutierrez 2026.05 退出 | 串流平台投入 |

## 生產 Pipeline

```
腳本/分鏡 → 圖片生成 (12-15張) → I2V → 後製編輯 → 配音/音效 → 串接輸出
```

- **Frame Chaining**: 前一片段末幀作為下一片段起始幀
- **60 秒以上**: 多場景 crossfade 串接是最實用方案
- **LTX Studio 自迴歸**: 可達~60秒連續生成

## ComfyUI + AnimateDiff

- **ComfyUI**: 119,981⭐ — 節點式 AI 引擎，支援 SD1.5/SDXL/FLUX/Hunyuan
- **AnimateDiff**: 12,183⭐ — ICLR2024 Spotlight，插入式動畫模組
- **典型 ComfyUI 動畫工作流**: Load Checkpoint → CLIP Text Encode → AnimateDiff Loader → AnimateDiff Sampler → KSampler → VAE Decode → Video Combine
- **ControlNet**: 33,985⭐ — Canny/Depth/OpenPose/Scribble/Tile

## 角色一致性方案優先級

1. 🥇 **共用參考圖 + I2V** — 最簡最有效
2. 🥈 **IP-Adapter** (22M參數) + AnimateDiff — 雙重約束
3. 🥉 **Face Swap 後製** (FaceFusion 29K⭐ / ReActor) — 補救方案
4. **ControlNet** (OpenPose/Canny/Depth) — 特定構圖控制
5. **Frame Chaining** — 長鏡頭連續
6. ❌ **純文字 prompt** — 不可靠

## 長片方案比較

| 方法 | 極限時長 | 複雜度 | 品質 | 成本 |
|:----|:---------|:-------|:-----|:-----|
| 多場景串接 + Crossfade | 理論無限 | 🟡中 | 🟢高 | 🟡中 |
| LTX Studio 自迴歸 | ~60秒 | 🟢低 | 🟡中 | 🟡中 |
| Frame Chaining | 理論無限 | 🔴高 | 🟢非常高 | 🔴高 |
| AnimateDiff 長序列 | ~8秒/批次 | 🔴高 | 🟡中 | 🟡中 |

## 市場訊號

- **Katzenberg** 預測 AI 取代 90% 動畫工作（HN 59 points）
- **Spiridellis Bros.** 獲 Google AI Futures Fund 等大額投資
- **Runway** 5000 萬用戶，Amazon/History Channel/Under Armour 使用案例
- **Sora 2026.04.26 關閉** — 閉源 API 依賴風險教訓

## 痛點

1. 🔴 **角色漂移** — 最嚴重，解決方案：共用參考圖 + IP-Adapter + negative prompt
2. 🟡 **動態一致性** — 大動(Motion)角色保留率僅 20-40%
3. 🟡 **成本** — 60 秒 API 模式 $10-50；自託管 GPU $1-3/小時
4. 🟠 **解析度不一致** — ffprobe 檢查後 ffmpeg 統一
5. 🟠 **閉源依賴風險** — Sora 前車之鑑

## 來源

- [Wikipedia: Text-to-video model](https://en.wikipedia.org/wiki/Text-to-video_model)
- [Wikipedia: Fable Studio](https://en.wikipedia.org/wiki/Fable_Studio)
- [Wikipedia: LTX Studio](https://en.wikipedia.org/wiki/LTX_Studio)
- [Runway 產品頁](https://runwayml.com/product)
- [Variety: Spiridellis Bros](https://variety.com/2025/digital/news/storybots-ai-animation-company-1236212345/)
- [AnimateDiff / IP-Adapter / ControlNet / FaceFusion（GitHub）](https://github.com/)
