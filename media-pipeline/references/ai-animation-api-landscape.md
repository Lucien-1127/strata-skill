# AI 動畫影片 API 市場格局（2026 年中）

> 研究日期：2026-07-09 | 來源：3 平行子代理深度爬取（官網、GitHub、Reddit、HN）

---

## 歐美 API 陣營

| API | 模型 | 最長時長 | 解析度 | 定價 | API 公開？ | SDK |
|:----|:----|:--------:|:------:|:-----|:---------:|:---:|
| **Runway** | Gen-4.5 | 15s | 4K | $15-95/月 | ✅ | 社群 Python |
| **Pika** | Pika 2.5 | 15s | 1080p | $10-90/月 | ✅ | ❌ |
| **Luma AI** | Ray 2 | 15s | 1080p | $20-80/月 | ✅ **最佳** | ✅ Python+JS |
| **Stability AI** | SVD/SV3D | 2-5s | 1080p | $20+/月 | ✅ **開源** | ✅ Python |
| **OpenAI Sora** | Sora 2.0 | **120s** | 4K | ? | ❌ **2026.9 終止** | — |
| **Haiper** | Haiper 2.0 | 10s | 1080p | $10-50/月 | ❌ 僅商業 | — |

### 關鍵結論（歐美）

- **最適合開發者串接**：Luma AI（Ray 2）— ReadMe 文件最完整、官方 Python/JS SDK、公開定價
- **最高真實感**：Sora（已關閉）> Runway Gen-4.5 ≈ Luma Ray 2 > Pika 2.5
- **唯一開源選項**：Stability AI（SVD/SV3D），可自託管但時長極短
- **Sora 教訓**：2026.4.26 關閉服務，API 2026.9 終止 — 閉源依賴風險高

---

## 中國/亞洲平台

| 平台 | 開發商 | 模型版本 | 最長時長 | API | 最低價 | 台灣可用性 |
|:----|:------|:--------|:--------:|:---:|:------|:----------|
| **Kling** | 快手 | Kling 4.0 | ~10s | ✅ 商務申請 | $2K/月起 | ✅ 英文界面可用 |
| **Vidu** | 生數科技 | Vidu Q3 + S1 | ~10s | ✅ **開放 REST** | 按量計費 | ✅ **免手機號** |
| **CogVideo** | 智譜 | CogVideoX-2B | ~6s | ✅ 開放 REST | 最便宜 | ✅ API 可用 |
| **Wan 萬相** | 阿里 | Wan 2.6 | **15s** | ✅ 百煉平台 | 按量計費 | ⚠️ 需阿里雲帳號 |
| **Jimeng 即夢** | 字節跳動 | Jimeng | ~10s | ❌ 無 API | 包月 | ❌ 需中國手機號 |
| **TopView 騰訊** | 騰訊 | HunyuanVideo | ~10s | ✅ 騰訊雲 | 按量 | ❌ 需實名認證 |

### 中國 vs 西方對比

| 維度 | 中國 | 西方 | 優勢 |
|:----|:---:|:---:|:----|
| 影片品質 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 西方 |
| **API 定價** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **中國低 50-70%** |
| **開源** | ⭐⭐⭐⭐ | ⭐⭐⭐ | **中國（CogVideoX/HunyuanVideo 已開源）** |
| **影片長度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **中國（Wan 2.6 可 15s）** |
| **聲畫同步** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中國 |
| API 文檔品質 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 西方 |
| 開發者體驗 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 西方 |
| **繁體中文** | ⭐⭐ | ⭐⭐⭐⭐ | 西方 |

### 對台灣開發者的建議

| 使用場景 | 推薦平台 |
|:---------|:---------|
| 最開放、文檔完善的 API | **Vidu** (platform.vidu.com) — 免手機號、多語言 |
| 最便宜、有開源模型 | **CogVideoX** (智譜) |
| 高品質影片生成 | **Kling** (需商務申請，最低 $2K/月) |
| 15 秒長影片 | **Wan 2.6** (阿里雲百煉平台) |
| 即時數位人互動 | **Vidu S1** |

---

## 業界生產 Pipeline

### 知名工作室技術路線

| 工作室 | 模式 | 工具鏈 |
|:------|:----|:-------|
| **Fable Studio** | AI Showrunner 自動劇集 | LLM Agent 敘事 + 多擴散模型視覺 |
| **Spiridellis Bros.** | 原創 IP 長片（Google AI Futures Fund 投資） | MJ→Runway Gen→Premiere→ElevenLabs |
| **LTX Studio** | 故事板式製作，近即時生成 | LTX-2 開源模型 + Google Veo 3 |
| **Runway Studios** | 5,000 萬用戶，AI 電影節 | Runway Gen-4.5 + Aleph 2.0 + Act-Two |
| **開源社群** | ComfyUI 工作流 | AnimateDiff + IP-Adapter + ControlNet + FaceFusion |

### 角色一致性方案（有效性排序）

1. ✅ **共用參考圖 I2V** — 最簡單、最有效
2. ✅ **IP-Adapter**（Tencent, 22M 參數, 6.6K⭐）
3. ✅ **Face Swap 後製**（FaceFusion, 29K⭐）
4. ✅ **ControlNet + 多重約束**（34K⭐）
5. ❌ 純文字 prompt — 不可靠

### Motion 難易度分級

| Motion 量 | 角色保留成功率 | 範例 |
|:---------|:--------------|:-----|
| 🟢 **微動** | 高 | 頭髮飄、呼吸、眨眼 |
| 🟡 **中動** | 中 | 走路、轉身、舉手 |
| 🔴 **大動** | 低 | 跑、跳、跳舞 |

### 60 秒以上長片製作

- **素材需求**：12-15 張核心圖片（AI 延伸生成模式）
- **串接方式**：ffmpeg concat + crossfade（硬切→角色漂移明顯）
- **進階方案**：LTX Studio 自迴歸技術可達 ~60 秒；Frame Chaining（末幀→次鏡錨點）可改善連貫性
- **成本估算**：API 模式約 $10-50/部（取決於場景數與模型）

### 預算分層 Pipeline

| 預算 | Pipeline | 說明 |
|:----|:---------|:-----|
| 🟢 $0-50/部 | SD/FLUX → AnimateDiff/ComfyUI → ffmpeg | 開源全自託管 |
| 🟡 $50-500/部 | MJ/FLUX → Runway/Pika/Vidu → Premiere → ElevenLabs | 混合模式 |
| 🔴 $500+/部 | 專業分鏡 → Runway+ComfyUI 定製 → 專業剪輯/調色 | 專業製作 |

### 業界痛點（依嚴重程度）

| 痛點 | 嚴重性 | 說明 | 緩解 |
|:----|:------:|:-----|:-----|
| 角色漂移 | 🔴 | 跨場景外觀不一致 | 共用參考圖 + IP-Adapter |
| 動態一致性 | 🟡 | 抖動/變形/閃爍 | guidance_scale↑, motion_bucket_id↓ |
| API 成本 | 🟡 | 每場景幾十元 | 開源自託管 / 排程生成 |
| 模型關閉風險 | 🟠 | Sora 教訓 | 避免單一閉源依賴 |
| 工會抵制 | 🟠 | WGA/SAG-AFTRA 反對 | 了解法律風險 |

---

## References

- 完整報告 1（歐美 API）：`/home/ysga1/ai-video-api-research.md`
- 完整報告 2（中國平台）：`/home/ysga1/asia-ai-video-platforms-report.md`
- 完整報告 3（產業 Pipeline）：`/home/ysga1/ai-animation-industry-deep-research.md`
- 本機 Agnes API：`~/.hermes/skills/media-pipeline/scripts/pipeline-feg.py`
- 姊妹專案 CineAgent：`~/CineAgent/run_pipeline.py`
