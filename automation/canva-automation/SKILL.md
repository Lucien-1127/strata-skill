---
name: canva-automation
description: Canva Connect API 自動化 — 設計/資產/匯出/自動填充操作
version: 1.0.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [canva, design, automation, api, oauth]
    related_skills: [agnes-prompt-architect]
---

# 🎨 Canva Connect API 自動化 (canva-automation)

## 觸發條件
用戶要求自動建立 Canva 設計、上傳圖片、批量匯出、自動填充模板、或整合 Canva 到工作流程。

## 前置準備

| 項目 | 說明 |
|:----|:------|
| Canva 帳號 | ✅ 需要付費帳號（Canva Pro 或 Enterprise） |
| Client ID + Secret | 從 `canva.com/developers/integrations` 取得 |
| OAuth 一次性授權 | 用戶需在瀏覽器手動授權一次，取得 refresh_token |
| Token 儲存 | 存於 `~/.hermes/env/canva.env` |

## 認證流程 (OAuth 2.0 PKCE)

### 一次性設定

```
① 在 canva.com/developers/integrations 建立 Connect API 整合
    → 取得 client_id + client_secret
② 用戶造訪授權 URL（需瀏覽器）：
    https://www.canva.com/api/oauth/authorize?code_challenge=<PKCE>&
    code_challenge_method=s256&scope=<scopes>&response_type=code&
    client_id=<ID>&redirect_uri=<REDIRECT_URI>&state=<anti-csrf>
③ 用戶同意 → 回傳 authorization_code
④ POST /v1/oauth/token 交換 access_token + refresh_token
⑤ refresh_token 永續使用（一次性換新，每次拿到新的）
```

### 自動化操作（不需瀏覽器）

```python
# 用 refresh_token 換新 access_token
POST /v1/oauth/token
{
  "grant_type": "refresh_token",
  "client_id": "...",
  "client_secret": "...",
  "refresh_token": "..."
}
# → 回傳新的 access_token + refresh_token
```

### Token 端點

| 端點 | 功能 |
|:----|:------|
| `POST /v1/oauth/token` | 交換 authorization_code 或 refresh_token |
| `POST /v1/oauth/introspect` | 驗證 token 有效性 |
| `POST /v1/oauth/revoke` | 撤銷 token |

## OAuth Scopes 參考

| Scope | 權限 | 用途 |
|:------|:-----|:------|
| `asset:read` | 讀取資產 metadata | 查詢已上傳圖片 |
| `asset:write` | 上傳/更新/刪除資產 | 上傳 Agnes 生成圖片到 Canva |
| `design:content:read` | 讀取設計內容 | 取得設計細節 |
| `design:content:write` | 建立設計 | 建立新設計 |
| `design:meta:read` | 讀取設計 metadata | 查詢設計清單 |
| `brandtemplate:content:read` | 讀取品牌模板內容 | 取得可填充欄位 |
| `brandtemplate:content:write` | 發布品牌模板 | 管理模板 |
| `folder:read` | 讀取資料夾 | 瀏覽設計目錄 |
| `folder:write` | 新增/移動資料夾 | 整理設計 |
| `comment:read` | 讀取評論 | 查看設計評論 |
| `comment:write` | 建立評論 | 回覆設計評論 |
| `profile:read` | 讀取使用者資訊 | 取得用戶資料 |

**重要**：scope 必須明確宣告，`asset:write` 不包含 `asset:read`，須雙雙宣告。

## 主要 API 端點

### Designs（設計）

| 方法 | 路徑 | 功能 |
|:----|:------|:------|
| GET | `/v1/designs` | 列出所有設計 |
| POST | `/v1/designs` | 建立新設計 |
| GET | `/v1/designs/{id}` | 取得設計 metadata |
| GET | `/v1/designs/{id}/pages` | 取得頁面資訊 |
| GET | `/v1/designs/{id}/export-formats` | 可匯出格式 |
| GET | `/v1/designs/{id}/dataset` | 自動填充欄位檢查 |

### Assets（資產上傳）

| 方法 | 路徑 | 功能 |
|:----|:------|:------|
| POST | `/v1/asset-uploads` | 非同步上傳本機檔案 |
| GET | `/v1/asset-uploads/{jobId}` | 查詢上傳進度 |
| POST | `/v1/url-asset-uploads` | 從 URL 上傳 |
| GET | `/v1/url-asset-uploads/{jobId}` | 查詢 URL 上傳進度 |
| GET | `/v1/assets/{assetId}` | 取得資產 metadata |
| PATCH | `/v1/assets/{assetId}` | 更新資產 metadata |
| DELETE | `/v1/assets/{assetId}` | 刪除資產 |

**上傳限制**：圖片 < 50MB (JPEG/PNG/HEIC/GIF/TIFF/WEBP)，影片 < 500MB

### Exports（匯出）

| 方法 | 路徑 | 功能 |
|:----|:------|:------|
| POST | `/v1/exports` | 創建匯出任務 |
| GET | `/v1/exports/{exportId}` | 查詢進度 + 下載 URL |

### Autofill（自動填充）

| 方法 | 路徑 | 功能 |
|:----|:------|:------|
| POST | `/v1/autofills` | 自動填充品牌模板 → 產生設計 |
| GET | `/v1/autofills/{jobId}` | 查詢填充進度 |

### 其他

| 方法 | 路徑 | 功能 |
|:----|:------|:------|
| POST | `/v1/folders` | 建立資料夾 |
| POST | `/v1/folders/move` | 移動項目 |
| POST | `/v1/merges` | 合併設計 |
| POST | `/v1/resizes` | 調整設計尺寸 |
| POST | `/v1/imports` | 匯入設計 |
| POST | `/v1/url-imports` | 從 URL 匯入 |
| GET | `/v1/users/me` | 使用者資訊 |
| GET | `/v1/users/me/profile` | 使用者檔案 |

## Hermes 整合架構

```
┌─ Hermes Agent ──────────────────────┐
│  skill: canva-automation            │
│  ├─ references/api-endpoints.md     │
│  ├─ scripts/auth.py                 │
│  ├─ scripts/upload.py               │
│  ├─ scripts/export.py               │
│  └─ scripts/autofill.py             │
├──────────────────────────────────────┤
│  config: ~/.hermes/env/canva.env    │
│    CANVA_CLIENT_ID=xxx              │
│    CANVA_CLIENT_SECRET=xxx          │
│    CANVA_REFRESH_TOKEN=xxx          │
└──────────────────────────────────────┘
```

## 建議工作流程（Agnes → Canva）

```python
# 1. Agnes 生成圖片 → 取得公開 URL
# 2. Canva URL Asset Upload → 上傳到 Canva 資產庫
# 3. Canva Autofill → 填入品牌模板產生設計
# 4. Canva Export → 匯出為 PNG/PDF
# 5. 下載或分享連結給使用者
```

## 計時參考

| 操作 | 預估時間 | 備註 |
|:----|:--------|:------|
| Token refresh | < 1 秒 | 每次呼叫前自動換新 |
| Asset upload (URL) | 2-5 秒 | 非同步，需輪詢 |
| Design create | 1-2 秒 | 同步回應 |
| Autofill | 5-15 秒 | 非同步，依場景數 |
| Export | 10-30 秒 | 非同步，依設計複雜度 |
| Resize (批量) | 5-10 秒 | 非同步 |

## 資源連結

| 資源 | 網址 |
|:----|:------|
| Developer Portal | `canva.com/developers/integrations` |
| Quickstart | `canva.dev/docs/connect/quickstart/` |
| Authentication | `canva.dev/docs/connect/authentication/` |
| OpenAPI Spec | `canva.dev/sources/connect/api/latest/api.yml` |
| Starter Kit (GitHub) | `github.com/canva-sdks/canva-connect-api-starter-kit` |
| MCP Server | `canva.dev/docs/connect/mcp-server/` |
| Scopes 列表 | `canva.dev/docs/connect/appendix/scopes/` |

## Pitfalls

- ❌ **初次授權必須瀏覽器互動**：OAuth PKCE 無法完全無頭化。解決方案：一次性授權取得 refresh_token 後儲存
- ❌ **MCP Server 不能操作 API**：Canva Dev MCP Server 是開發輔助工具（查文件/UI Kit），不是 Connect API 執行層
- ❌ **Scope 不自動繼承**：`asset:write` 不包含 `asset:read`，每個 scope 必須明確宣告
- ❌ **選擇正確的整合類型**：Canva Developer Portal 有兩種整合 — **Canva Apps**（編輯器內嵌，需前端程式碼+翻譯）和 **Connect API**（後端 REST API，僅需 Client ID+Secret）。千萬別選錯，否則會看到「代碼上傳」「Translations」等無關設定頁面。
- ✅ **Redirect URI 可掛現有 nginx**：不需 ngrok 或另開伺服器。在既有 server block 加 `location = /canva-callback { ... }` 即可接收授權碼。用戶授權後複製瀏覽器網址列（含 `?code=xxx`）貼回。詳見 `references/oauth-callback-nginx.md`。
- ✅ **refresh_token 永續**：一次性使用，每次換新會給新的 refresh_token
- ✅ **非同步作業需輪詢**：上傳/匯出/autofill 都是非同步，需輪詢 jobId
- ✅ **OpenAPI Spec 可生成 client SDK**：`canva.dev/sources/connect/api/latest/api.yml` 可用 openapi-generator
