---
name: idol-video-pipeline
description: 角色參考圖→影片流水線，四階段審核制
version: 1.0.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [video, image, pipeline, anime, idol, workflow]
    related_skills: [media-pipeline, agnes-quota-router, img2vid-character, canva-connect]
---

# 🎤 角色影片流水線 (Idol Video Pipeline)

## 觸發條件
用戶給你一張角色圖片，並指定影片主題（如「動畫偶像唱歌」）

## 四階段工作流程

```
用戶發圖 + 主題
    │
    ├─ Phase 1: 腳本 ──── 你寫分鏡腳本 → 傳給用戶審核
    │
    ├─ Phase 2: ✅ 用戶確認腳本
    │
    ├─ Phase 3: 生圖 ──── 用 delegate_task 派子代理跑，不佔對話
    │                     完成後傳圖給用戶審核
    │
    ├─ Phase 4: ✅ 用戶確認圖片
    │
    └─ Phase 5: 影片 ──── 用 delegate_task 派子代理跑
                          完成後傳最終影片給用戶
```

## 關鍵規則

### 圖片生成 (Phase 3)
- **使用用戶原始圖片**作為 img2img 輸入（base64 Data URI）
- 不要先做 img2img 預處理再拿來用 — 直接餵原圖
- 設定 `"size": "576x1024"` (9:16 直式 720p)
- **負面提示詞必須包含角色保留限制**
- 每場景用 `extra_body.image: [data_uri]` + 各自場景 prompt
- 用 `delegate_task` 跑 — 不擋主對話

### 影片生成 (Phase 5)
- 使用用戶確認的圖片 URL（來自 Agnes 輸出，public URL）
- 設定 `"width": 576, "height": 1024` (9:16)
- **負面提示詞必須包含角色保留限制**
- 輪詢超時設 **600 秒**
- 用 `delegate_task` 跑 — 不擋主對話
- 多場景用 ffmpeg concat 串接，可選 crossfade
- 輪詢回應的影片 URL 在 `url` 欄位（非 `remixed_from_video_id`）

### 子代理委派 (delegate_task)
- 子代理內要包含：Agnes API key 讀取、圖片生成、URL 保存
- 完成後子代理回傳圖片 URL list
- 主代理收到後傳給用戶審核

## API 端點
- 圖片: `POST https://apihub.agnes-ai.com/v1/images/generations` (model: `agnes-image-2.1-flash`)
- 影片: `POST https://apihub.agnes-ai.com/v1/videos` (model: `agnes-video-v2.0`)
- 影片輪詢: `GET https://apihub.agnes-ai.com/agnesapi?video_id=<ID>&model_name=agnes-video-v2.0`
- 金鑰路徑: `~/.hermes/env/agnes.env` → `AGNES_API_KEY`

## 腳本範本 (4 場景 idol 演唱會)

| # | 場景 | 畫面描述 | 運鏡 |
|:-:|------|---------|:----:|
| ① | 開場 — 舞台登場 | 聚光燈下登場，舞台煙霧，手握麥克風 | 低角度推近 |
| ② | 主歌 — 深情歌唱 | 麥克風近距離特寫，眼神含光 | 緩慢推鏡 |
| ③ | 副歌 — 熱情舞蹈 | 全身舞動，彩色燈光，彩帶紛飛 | 中景跟隨 |
| ④ | 尾聲 — 感謝鞠躬 | 鞠躬謝幕，全場燈光匯聚 | 全景拉遠 |

## 計時參考
| 階段 | 單張/單段 | 4 場景總計 |
|:----|:---------|:----------|
| 文生圖 | ~35 秒 | ~2.5 分 |
| 圖生影 | ~70 秒 | ~5 分 |
| ffmpeg 串接 | ~5 秒 | ~5 秒 |

## 相關技能
- `img2vid-character` — 圖生影角色一致性提示詞架構（角色保留三層結構 + 負面詞模板）
- `media-pipeline` — 執行腳本與 ffmpeg 串接
- `agnes-quota-router` — API 路由與配額管理
- `agnes-prompt-architect` — 通用提示詞架構
- `canva-connect` — Canva API 整合（可選，品牌設計輸出）

## 提示詞規則（務必遵循）

所有圖生影 prompt 必須遵循：

1. **三層結構**：保留層→動態層→場景層
2. **Motion 最小主義**：只動頭髮 vs 全身跳舞 → 前者成功率更高
3. **角色保留負面詞必須加**（完整列表在 `img2vid-character` 技能）

## 執行腳本
- `media-pipeline/scripts/idol-video.py` — 角色參考圖→影片專用腳本
- `media-pipeline/scripts/pipeline-concat.py` — 通用多場景串接腳本

## Pitfalls
- ❌ 不要先用 img2img 預處理角色圖 — 角色會被 AI 改動
- ❌ 不要用 `remixed_from_video_id` — 用 `url` 欄位
- ❌ 不要在主對話中同步跑 — 用 delegate_task
- ❌ 503 錯誤必須重試（指數退避）
- ✅ 一定要加角色保留負面提示詞
- ✅ 一定要設 9:16 比例 (576x1024)
- ✅ 影片輪詢 timeout 設 600s
