# 歐美 AI 影片生成 API 研究（2026-07-09）

> 爬取來源：Runway/Pika/Luma/Haiper/Stability/Sora 官網定價頁面、API Docs、LLMs.txt

## 定價與規格對照表

| API | 模型 | 最長時長 | 解析度 | 月費 | API 公開 |
|:----|:----|:--------:|:------:|:----|:--------:|
| Runway | Gen-4.5 | 15s | 4K | $15-95/月 | ✅ 付費方案 |
| Pika | Pika 2.5 | 15s | 1080p | $10-90/月 | ✅ 付費方案 |
| Luma | Ray 2 | 15s | 1080p | $20-80/月 | ✅ Python+JS SDK 最佳 |
| Stability | SVD/SV3D | 2-5s | 1080p | $20+/月 | ✅ 開源可自託管 |
| OpenAI Sora | Sora 2.0 | 120s | 4K | — | ❌ 2026.9 API 終止 |
| Haiper | Haiper 2.0 | 10s | 1080p | $10-50/月 | ❌ 僅商業合作 |

## 串接難易度

| 服務 | API 文件 | SDK | 難度 |
|:----|:---------|:---|:-----|
| Luma AI | ⭐⭐⭐⭐⭐ ReadMe 完整 | Python + JS | 低（最推薦） |
| Runway | ⭐⭐⭐ Zendesk 託管 | 無官方 SDK | 中 |
| Pika | ⭐⭐⭐ Web 頁面 | 無官方 SDK | 中 |
| Stability | ⭐⭐⭐⭐ Restful | Python | 低 |

## 品質評分

| 維度 | 最佳 | 備註 |
|:----|:----|:-----|
| 真實感 | Sora > Runway Gen-4.5 > Luma Ray 2 > Pika 2.5 | |
| 動態一致性 | Gen-4.5 大幅改善，仍偶有變形 | |
| 角色保持 | Runway Reference Image 有效 | |
| 提示詞遵循 | Runway/Luma 精確 | |

## 知名客戶

- Runway: Lionsgate（合作訓練）、Nike、Adidas、Amazon、History Channel
- Pika: 5500 萬美元 A 輪
- Sora: 2026-04-26 關閉，API 2026-09 終止 — 閉源依賴風險的重大教訓

## 底層技術

- **DiT (Diffusion Transformer)** 已成主流（Sora 論文原創者、Runway Gen-4、Luma Ray 2）
- Stability 仍用 3D-UNet + Temporal Attention
- Pika 走輕量 Video Diffusion 路線

## 對目前 pipeline 的影響

- Agnes Video V2.0 的品質介於 Stability SVD 和 Pika 之間
- 若需升級：Luma Ray 2（API 最佳）或 Runway Gen-4.5（品質最佳）
- 開源備援：ComfyUI + AnimateDiff + IP-Adapter + ControlNet
