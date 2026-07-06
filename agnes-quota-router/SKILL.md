---
name: agnes-quota-router
description: 2-tier router — Agnes for image/video gen, all else DeepSeek
version: 0.2.0
author: Hermes
metadata:
  hermes:
    tags: [Agnes, Routing, Quota, Image, Video]
---

# Agnes AI Token Plan 路由排程

Agnes AI 僅用於圖片生成、影片生成（多模態產出，強制走 Agnes）。  
所有其他任務（文字、推理、程式碼、Vision分析等）直接走 DeepSeek。

## 方案概覽

| 項目 | 數值 |
|------|------|
| **方案** | Agnes Token Plan Starter |
| **配額** | 1,500 req / 5h（滑動窗口） |
| **到期** | 2026-07-29 |
| **可用模型** | Agnes-Image-2.1-Flash、Agnes-Video-V2.0 |
| **備用 Provider** | DeepSeek V4 Flash / V4 Pro |

## 路由策略（2-Tier）

```
請求進入
  │
  ├─ Tier 1（產出類別）─→ Agnes（強制）
  │    圖片生成（文生圖 / 圖生圖）
  │    影片生成（文生影 / 圖生影）
  │
  └─ Tier 2（其餘一切）─→ DeepSeek
       文字對話、推理、程式碼
       Vision / 圖片理解
       摘要、翻譯、分類
       Agent 工作流
```

### 核心邏輯

```
if task in [image_generation, image_editing, video_generation]:
    → Agnes（強制，消費 quota）
else:
    → DeepSeek（不消費 Agnes quota）
```

Agnes 配額僅留給多模態產出 — 只剩 1 次 quota 也能產一張圖。

## 配額監控

依賴 **cronjob 輕量監控**（詳見對應的 cronjob「API 狀態監視器」）：定時檢查 Agnes API 配額 + DeepSeek 端點狀態。

## API 端點參考

Agnes AI 有獨立的圖片與影片端點，完整源碼請參考官方 API 文檔。

| 資源 | 端點 | 模型 | 備註 |
|:-----|:-----|:-----|:-----|
| **圖片生成** | `POST /v1/images/generations` | `agnes-image-2.1-flash` | base_url=`https://apihub.agnes-ai.com/v1` |
| **影片生成** | `POST /v1/videos` | `agnes-video-v2.0` | 非同步任務，回傳 task_id |
| **影片狀態查詢** | `GET /agnesapi?video_id=<ID>&model_name=agnes-video-v2.0` | - | 推薦方式 |
| **影片狀態查詢(備用)** | `GET /v1/videos/<TASK_ID>` | - | 傳統方式 |

### 圖片生成（`POST /v1/images/generations`）

| 操作 | 必要欄位 |
|:-----|:---------|
| **文生圖** | `model`（agnes-image-2.1-flash）、`prompt`、`size` |
| **圖生圖** | + `extra_body.image`（陣列，每項為公開 URL 或 `data:image/png;base64,...`） |
| **輸出格式** | `extra_body.response_format` = `"url"` 或 `"b64_json"` |
| **Base64 輸出**（文生圖） | `return_base64: true`（頂層參數） |

> 圖生圖建議用 Base64 Data URI。外部 CDN（如 Wikimedia）可能被拒絕。

### 影片生成（`POST /v1/videos`）

| 操作 | 說明 |
|:-----|:-----|
| **建立任務** | `POST /v1/videos` → 回傳 `task_id` + `video_id` |
| **查詢結果** | `GET /agnesapi?video_id=<ID>&model_name=agnes-video-v2.0` |
| **影片 URL 欄位** | `remixed_from_video_id`（不是 `url`） |
| **幀數規則** | `8n + 1`，最大值 441。15秒@24fps=361 |
| **解析度** | 自動正規化到 480p/720p/1080p，以回應 `size` 為準 |

### 圖生影 Pipeline（已實測驗證）

```
文生圖 (agnes-image-2.1-flash)
  → 取得 platform-outputs.agnes-ai.space URL
  → 立即用該 URL POST /v1/videos (圖生影, agnes-video-v2.0)
```

| 結果 | 說明 |
|:----|:-----|
| ✅ | 文生圖 URL → 直接餵 POST /v1/videos image 參數 → 成功 3.9MB 5秒影片 |
| ❌ | Base64 Data URI → 影片 API **不接受**（但圖片 API 接受） |
| ❌ | 外部 CDN URL（如 Wikimedia）→ 圖片 API 拒絕 |
| ⏱ | 5秒影片約 2分鐘；15秒約 5分鐘 |

**關鍵差異**：圖生影的 `image` 參數是**單一字串**（必須是公開 URL）。圖生圖的 `extra_body.image` 是**陣列**（接受 URL 或 Base64 Data URI）。

## 風險

| 風險 | 說明 |
|:----|:-----|
| 📅 **到期日** | 2026-07-29 後需續約或降級 20 RPM 免費方案 |
| 🔄 **滑動窗口** | 每 5h 重置，非每日。用完需等最早請求滿 5h 才釋放 |
| 📊 **平行消耗** | 5 個平行文生圖消耗 ~5 次配額；完整動畫產出 ~10-20 次（含輪詢） |

## 監控整合

- **cronjob**：`API 狀態監視器` — 定時檢查 Agnes 配額 + DeepSeek 端點
- **警報閾值**：Agnes 配額 < 100 → 🔴 緊急通知；< 300 → 🟡 注意
