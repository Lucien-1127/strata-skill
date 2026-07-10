# Canva Connect API 研究報告

> 研究日期：2026-07-06
> 資料來源：https://www.canva.dev/docs/connect/

## 概觀

Canva Connect API 是 RESTful API，版本 `2024-06-18`，提供 **58 個端點**：

| 領域 | 端點數 | 說明 |
|------|--------|------|
| OAuth | 3 | Token 生成、驗證、撤銷 |
| OIDC | 2 | 使用者身份驗證 |
| Assets | 6 | 上傳、管理圖片/影片資產 |
| Designs | 7 | 建立、讀取、管理設計 |
| Design Imports | 4 | 從外部匯入設計 |
| Exports | 2 | 匯出設計為各種格式 |
| Autofill | 2 | 自動填充品牌模板 |
| Brand Templates | 4 | 品牌模板 CRUD |
| Comments | 6 | 設計評論管理 |
| Folders | 7 | 資料夾 CRUD 與移動 |
| Merges | 2 | 合併設計 |
| Resizes | 2 | 調整設計尺寸 |
| Analytics | 4 | 設計分析數據 |
| Users | 3 | 使用者資訊 |
| Webhooks | (通過 Developer Portal 設定) | 事件通知 |

## 認證流程

OAuth 2.0 Authorization Code with PKCE (SHA-256)：

1. 註冊整合 → client_id + client_secret
2. 用戶授權 URL：`https://www.canva.com/api/oauth/authorize?code_challenge=<PKCE>&code_challenge_method=s256&scope=<scopes>&response_type=code&client_id=<ID>&redirect_uri=<URL>`
3. Token 端點：`POST /v1/oauth/token`
4. Token 驗證：`POST /v1/oauth/introspect`
5. Token 撤銷：`POST /v1/oauth/revoke`

### 關鍵限制

- Token 交換**必須從後端伺服器發出**（CORS 阻擋瀏覽器端）
- 用戶授權**必需**（瀏覽器手動操作）
- refresh_token **一次性使用**，每次刷新後給新的
- 初次授權後可完全自動化後續操作（refresh_token 持續換新）

## Canva Dev MCP Server

- 套件：`@canva/cli` (npm)，最新 v2.6.0
- MCP SDK：`@modelcontextprotocol/sdk` 1.27.1
- 指令：`npx -y @canva/cli@latest mcp`
- 傳輸方式：stdio（本地端）
- 支援：Cursor / Claude Desktop / Claude Code / VS Code

**MCP Server 定位是開發輔助工具**（查文件、App UI Kit、SDK），**不能操作 Connect API**。

## 自動化可行性

| 操作 | 可行性 |
|------|--------|
| 批量建立設計 | ✅ Autofill API + Brand Template |
| 批量上傳圖片 | ✅ Asset Upload API（非同步） |
| 批量匯出設計 | ✅ Export API |
| 批量調整尺寸 | ✅ Resize API |
| 批量合併設計 | ✅ Merge API |
| 定時報告 | ✅ Analytics API |
| Webhook 監聽 | ✅ 設計變更通知 |

## 整合建議

**最佳方案：Hybrid**
- MCP Plugin：提供文件查詢能力
- Hermes Skill：封裝 REST API 操作（含 OAuth token 自動管理）

## 關鍵資源

| 資源 | 網址 |
|------|------|
| Developer Portal | https://www.canva.dev/developers/ |
| 快速入門 | https://www.canva.dev/docs/connect/quickstart/ |
| 認證文件 | https://www.canva.dev/docs/connect/authentication/ |
| MCP Server | https://www.canva.dev/docs/connect/mcp-server/ |
| Designs API | https://www.canva.dev/docs/connect/api-reference/designs/ |
| Assets API | https://www.canva.dev/docs/connect/api-reference/assets/ |
| Scopes | https://www.canva.dev/docs/connect/appendix/scopes/ |
| OpenAPI Spec | https://www.canva.dev/sources/connect/api/latest/api.yml |
| Starter Kit | https://github.com/canva-sdks/canva-connect-api-starter-kit |
