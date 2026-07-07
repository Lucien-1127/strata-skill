# 🎬 Agnes Video V2.0 — 官方 API 參考文件
# 來源: https://wiki.agnes-ai.com/llms.txt
# 模型: agnes-video-v2.0
# 創建端點: POST https://apihub.agnes-ai.com/v1/videos
# 查詢端點(推薦): GET https://apihub.agnes-ai.com/agnesapi?video_id=<ID>
# 查詢端點(舊版): GET https://apihub.agnes-ai.com/v1/videos/<TASK_ID>

## 支持能力
- 文生視頻: text → video
- 圖生視頻: image URL → video (image 為單一字串)
- 多圖視頻: extra_body.image 陣列
- 關鍵幀動畫: extra_body.mode = "keyframes"

## 必填參數
- model: agnes-video-v2.0
- prompt: 文本描述

## 可選參數
| 參數 | 說明 |
|:-----|:-----|
| image | 單字串 (圖生影) 或 extra_body.image 陣列 (多圖/關鍵幀) |
| mode | "keyframes" 等 |
| height/width | 默認 768x1152，自動標準化到 480p/720p/1080p |
| num_frames | ≤441, 8n+1 規則 |
| frame_rate | 1-60 |
| seed | 可復現種子 |
| negative_prompt | 反向提示詞 |

## 幀數-時長對照 (推薦 @24fps)
| 目標時長 | num_frames |
|:--------|:----------|
| ~3秒 | 81 |
| ~5秒 | 121 |
| ~10秒 | 241 |
| ~18秒(max) | 441 |

## 圖生影關鍵差異
- 圖生影 image 參數是單一字串 (必須公開 URL)
- 圖生圖 extra_body.image 是陣列 (URL 或 Base64 Data URI)
- Base64 Data URI → 影片 API 不接受! 必須用文生圖輸出的公開 URL

---
## Pipeline (已實測) — 查詢結果欄位更新

文生圖 (agnes-image-2.1-flash) → platform-outputs URL
→ POST /v1/videos image=該URL (圖生影)
→ 輪詢 /agnesapi?video_id=<ID> 直到 status=completed

**實測發現 (2026-07-06)**：
- ✅ 結果影片在 `url` 欄位（實際下載連結）
- ❌ `remixed_from_video_id` 此次測試為 `null`，**不要依賴**
- 正確取得方式：`data.get("url", "") or data.get("remixed_from_video_id", "")`

## 輸出格式

```json
{
  "id": "video_xxxxxx",
  "status": "completed",
  "url": "https://platform-outputs.agnes-ai.space/videos/.../video_xxxxxx.mp4",
  "remixed_from_video_id": null,
  "seconds": "4.7",
  "size": "1088x832"
}
```
