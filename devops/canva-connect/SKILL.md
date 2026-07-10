---
name: canva-connect
description: Canva Connect API 整合 — OAuth 認證、設計/資產操作、自動化腳本
version: 1.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [canva, api, automation, design, oauth]
    related_skills: [idol-video-pipeline, img2vid-character]
status: stable
---

# Canva Connect API 整合

## 用途

透過 Canva Connect API 以程式化方式操作 Canva 設計：
- 建立/讀取設計
- 上傳/管理資產（圖片、影片）
- 自動填充品牌模板批量產生設計
- 匯出 PNG/PDF
- 調整尺寸、合併設計

## 前置條件

1. Canva 付費帳號（已確認 ✅）
2. **MFA（多因素驗證）必須先啟用** — 在 canva.com 帳號設定→安全中啟用，否則不能建立整合
3. 在 [Canva Developer Portal](https://www.canva.com/developers/integrations) 建立 Connect API 整合
   ⚠️ 開發者入口**僅支援桌面版瀏覽器**，手機無法使用
4. 取得 **Client ID** + **Client Secret**

## ⚠️ 關鍵陷阱：開發者入口登入

### 正確路徑

| 目的 | 網址 | 說明 |
|:-----|:-----|:------|
| 開發者首頁 | `https://www.canva.dev/developers/` | 開發者專屬，與 canva.com 不同域 |
| 整合管理 | `https://www.canva.com/developers/integrations` | 登入後管理既有/新建整合 |
| 官方文件 | `https://www.canva.dev/docs/connect/` | API 參考、Quickstart |

**常見陷阱：** 使用者在 canva.com 上找「開發者」會進到一般帳號設定（頭像、安全、團隊），不是開發者頁面。

### Google 登入問題

若 Canva 使用 Google SSO 登入：
1. 先在 `canva.com` 用 Google 登入
2. 同一瀏覽器開新分頁 → `https://www.canva.com/developers/integrations`
3. 應自動通過認證

若不行，檢查：
- ✅ MFA 已啟用（必要條件）
- ✅ 是否在正確 URL（不是 canva.com/settings）

### Integration 類型選擇

| 類型 | 需求 | 審核 | 適用 |
|:-----|:------|:------|:------|
| **Public** | 一般 Canva 帳號 | ✅ 需審核才能上線 | 個人帳號 |
| **Private** | Canva Enterprise 方案 | ❌ 不需審核 | 團隊內部用 |

## 建立整合流程

| 步驟 | 操作 | 注意 |
|:----:|:------|:------|
| ① | 進 `https://www.canva.com/developers/integrations` | 桌面版瀏覽器 |
| ② | 點「Create an integration」 | |
| ③ | **選 Public**（不要選 Private） | ❌ Private 需要 Enterprise |
| ④ | 打勾同意條款 | |
| ⑤ | 設定名稱（如「智研自動化」） | |
| ⑥ | 複製 **Client ID** → 存好 | |
| ⑦ | 點「Generate secret」→ 複製 **Secret** | 🔴 關閉頁面後無法再次查看 |
| ⑧ | Scopes → 勾需要權限 | |
| ⑨ | Authentication → 設定 Redirect URI | 見下方 |

### Redirect URI

Callback 端點（NGINX）：
```nginx
location = /canva-callback {
    add_header Content-Type text/html;
    return 200 '<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2em;background:#0f172a;color:#e2e8f0"><h2>✅ 授權成功</h2><p>請複製整個網址列內容貼給 Hermes</p><pre id="code" style="background:#1e293b;padding:1em;border-radius:8px;word-break:break-all;color:#22c55e"></pre><script>const url = window.location.href; document.getElementById("code").textContent = url;</script></body></html>';
}
```

## 認證流程

Canva Connect API 使用 **OAuth 2.0 Authorization Code with PKCE (SHA-256)**：

```
① 開發者註冊 → 取得 client_id + client_secret
       ↓
② 用戶瀏覽器授權一次（必須）
   https://www.canva.com/api/oauth/authorize?code_challenge=...&scope=...&client_id=...
       ↓
③ 收到 authorization_code（透過 redirect URI 回傳）
       ↓
④ POST https://api.canva.com/rest/v1/oauth/token
   用 Basic Auth (client_id:client_secret base64) 交換
   → 取得 access_token + refresh_token
       ↓
⑤ 用 refresh_token 持續在背景換新 access_token（一次性，每次給新的）
       ↓
⑥ 用 access_token 呼叫 REST API
```

### PKCE 參數產生（Python）

```python
import hashlib, base64, secrets
code_verifier = secrets.token_urlsafe(96)[:128]
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
state = secrets.token_urlsafe(96)
```

### Token 交換

```bash
# authorization_code → tokens
curl -X POST https://api.canva.com/rest/v1/oauth/token \
  -H "Authorization: Basic $(echo -n 'client_id:client_secret' | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=<CODE>&code_verifier=<VERIFIER>&redirect_uri=<REDIRECT>"

# refresh_token → new tokens
curl -X POST https://api.canva.com/rest/v1/oauth/token \
  -H "Authorization: Basic $(echo -n 'client_id:client_secret' | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=<TOKEN>"
```

## OAuth Scopes

| Scope | 權限 |
|-------|------|
| `asset:read` | 讀取資產 metadata |
| `asset:write` | 上傳/更新/刪除資產 |
| `design:content:read` | 讀取設計內容 |
| `design:content:write` | 建立設計 |
| `design:meta:read` | 讀取設計 metadata |
| `brandtemplate:content:read` | 讀取品牌模板內容 |
| `brandtemplate:content:write` | 發布品牌模板 |
| `folder:read` | 讀取資料夾 |
| `folder:write` | 新增/移動資料夾 |
| `comment:read` | 讀取評論 |
| `comment:write` | 建立評論 |
| `profile:read` | 讀取使用者資訊 |

Scope 需**明確宣告**，`asset:write` 不會自動包含 `asset:read`。

## API 端點

完整 OpenAPI spec: `https://www.canva.dev/sources/connect/api/latest/api.yml`
Starter Kit (GitHub): `https://github.com/canva-sdks/canva-connect-api-starter-kit`

### 核心端點

| 方法 | 路徑 | 功能 |
|------|------|------|
| POST | `/v1/oauth/token` | 取得/刷新 access_token |
| POST | `/v1/designs` | 建立設計 |
| GET | `/v1/designs/{id}` | 讀取設計 |
| POST | `/v1/asset-uploads` | 非同步上傳資產 |
| GET | `/v1/asset-uploads/{jobId}` | 查詢上傳進度 |
| POST | `/v1/autofills` | 自動填充品牌模板 |
| POST | `/v1/exports` | 匯出設計 |
| GET | `/v1/exports/{id}` | 查詢匯出進度 |
| POST | `/v1/resizes` | 調整尺寸 |
| POST | `/v1/merges` | 合併設計 |

### 上傳限制

- 圖片：< 50 MB（JPEG/PNG/HEIC/GIF/TIFF/WEBP）
- 影片：< 500 MB（M4V/MKV/MP4/MPEG/QuickTime/WebM）

## 自動化流程

```
[一次性] 用戶瀏覽器授權 → 取得 refresh_token
    ↓
[排程] 用 refresh_token 換新 access_token
    ↓
[排程] 呼叫 Autofill API 批量產生設計
    ↓
[排程] 呼叫 Export API 匯出 PNG/PDF
    ↓
[排程] 下載匯出檔案
```

所有寫入操作都支援非同步（async job），適合批量處理。

## 金鑰管理

建立 `~/.hermes/env/canva.env`：
```bash
CANVA_CLIENT_ID=your_client_id
CANVA_CLIENT_SECRET=your_client_secret
CANVA_REFRESH_TOKEN=your_refresh_token
```
權限 `chmod 600`。

## 開發資源

- Developer Portal: `https://www.canva.dev/developers/`
- Quickstart: `https://www.canva.dev/docs/connect/quickstart/`
- Auth docs: `https://www.canva.dev/docs/connect/authentication/`
- MCP Server: `https://www.canva.dev/docs/connect/mcp-server/`
- Designs API: `https://www.canva.dev/docs/connect/api-reference/designs/`
- Assets API: `https://www.canva.dev/docs/connect/api-reference/assets/`
- Scopes: `https://www.canva.dev/docs/connect/appendix/scopes/`
- OpenAPI: `https://www.canva.dev/sources/connect/api/latest/api.yml`
- Creating Integrations: `https://www.canva.dev/docs/connect/creating-integrations/`

## Pitfalls（踩坑記錄）

### 設定前

- ❌ **MFA 必須先啟用** — cannot create integration without it
- ❌ **Private 整合需要 Enterprise 方案** — 一般 Canva Pro/Free 只能選 **Public**
- ❌ **初次授權必須瀏覽器互動** — OAuth PKCE 無法完全無頭化
- ❌ **開發者入口手機不能用** — 桌面瀏覽器限定
- ❌ **`canva.dev` vs `canva.com` 域混淆** — Google SSO 要先在 canva.com 登入，再去 `canva.com/developers/integrations`
- ❌ **`localhost` 不可作為 redirect URI** — 用 `http://127.0.0.1:3000`
- ❌ **Canva Apps 頁面（代碼上傳、Translations）不是 Connect API** — 兩者不同。Connect API 不需要上傳程式碼

### 設定中

- ❌ **Secret 只顯示一次** — 生成立即複製，關閉頁面後無法再次查看
- ✅ **Scope 不自動繼承** — 每個 scope 要明確宣告

### 設定後

- ❌ **refresh_token 一次性** — 每次刷新後給新的，舊的失效
- ❌ **Token 交換必須從後端伺服器** — 瀏覽器端 CORS 阻擋
- ✅ **非同步作業需輪詢 jobId**
- ✅ **MCP Server 是開發輔助工具，不是 API 執行層**