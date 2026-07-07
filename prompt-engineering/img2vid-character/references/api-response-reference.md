# 圖生影 API 實際回應結構 — 實測記錄

> 來源：session 2026-07-06，Agnes Video V2.0，ti2vid 模式

## 成功回應（建立任務）

```json
{
  "id": "task_YOUR_TASK_ID",
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "object": "video",
  "model": "agnes-video-v2.0",
  "status": "queued",
  "progress": 0,
  "created_at": 1783355603,
  "seconds": "5.0",
  "size": "1088x832"
}
```

## 完成回應（輪詢結果）

```json
{
  "completed_at": 1783355674,
  "created_at": 1783355603,
  "error": null,
  "id": "video_64dd22b232d2493c8ad2bcffb62c82b1",
  "internal_status": "completed",
  "model": "agnes-video-v2.0",
  "object": "video",
  "perf_infer_s": 68.23,
  "perf_params": {
    "frame_rate": 24,
    "height": 832,
    "num_frames": 113,
    "num_inference_steps": 8,
    "seed": 106832,
    "width": 1088
  },
  "progress": 100,
  "remixed_from_video_id": null,
  "request_params": {
    "image": "https://platform-outputs.agnes-ai.space/images/.../output.png",
    "mode": "ti2vid",
    "negative_prompt": "different character, face change, ...",
    "num_frames": 121,
    "prompt": "Anime idol girl standing on illuminated stage..."
  },
  "seconds": "4.7",
  "size": "1088x832",
  "status": "completed",
  "url": "https://platform-outputs.agnes-ai.space/videos/agnes-video-v2.0/video_64dd22b232d2493c8ad2bcffb62c82b1.mp4"
}
```

## 關鍵欄位對照

| 用途 | 欄位 | 備註 |
|:----|:-----|:------|
| 任務建立後查詢用 ID | `video_id` | 輪詢時傳入 |
| 最終影片 URL | **`url`** | ✅ 正確欄位 |
| 最終影片 URL（舊版） | `remixed_from_video_id` | ❌ 常為 null，不要用 |
| 實際時長 | `seconds` | 字串，如 "4.7" |
| 實際解析度 | `size` | 如 "1088x832" |
| 推論耗時（秒） | `perf_infer_s` | 約 68 秒 (5秒影片) |
| 實際使用的參數 | `perf_params` | API normalize 後的值 |
| 請求原始參數 | `request_params` | 除錯用 |

## 比例 normalize 行為

當請求的 width/height 不符合標準比例時，API 會自動 mapping：

```json
"size_mapping": {
  "adjusted": true,
  "height": 832,
  "message": "Input size 1152x768 was mapped to nearest preset 720p/4:3 (1088x832)",
  "ratio": "4:3",
  "resolution": "720p",
  "width": 1088
}
```

**必須明確設 `width: 576, height: 1024`** 才能正確輸出 9:16 直式。省略或設錯比例會變成 4:3。

## 錯誤碼

| 錯誤 | HTTP | 處理方式 |
|:-----|:-----|:---------|
| API key 錯誤 | 401 | 檢查 ~/.hermes/env/agnes.env |
| 服務忙碌 | **503** | 指數退避重試 (2/4/8/16/32s × 5 次) |
| 請求參數錯誤 | 400 | 檢查 num_frames (8n+1) / size 格式 |
| 影片 URL 無效 | 404 | 確認 video_id 正確 |
| 伺服器錯誤 | 500 | 重試 |
