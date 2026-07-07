# Canva Connect API 研究報告

> 研究日期：2026-07-06
> 來源：https://www.canva.dev/docs/connect/
> OpenAPI Spec: https://www.canva.dev/sources/connect/api/latest/api.yml

## 概觀

Canva Connect API 提供 58 個 REST 端點，涵蓋：
- OAuth (3), OIDC (2), Assets (6), Designs (7), Design Imports (4)
- Exports (2), Autofill (2), Brand Templates (4), Comments (6)
- Folders (7), Merges (2), Resizes (2), Analytics (4)
- Users (3), Webhooks (透過 Developer Portal)

## 認證

OAuth 2.0 Authorization Code + PKCE (SHA-256)
- 初次授權：用戶瀏覽器手動同意
- 後續：refresh_token 持續換新 access_token
- refresh_token 一次性使用，每次換新後取得新的 refresh_token

## CLI/無頭化

部分可行。初次授權需瀏覽器，但取得 refresh_token 後可完全 server-to-server。

## MCP Server

`npx -y @canva/cli@latest mcp` — 僅供開發輔助（文件查詢/UI Kit），**不能操作 Connect API**。
支援 Cursor/Claude Desktop/Claude Code/VS Code。

## 自動化批量操作

✅ Autofill + Brand Template → 批量產生設計
✅ Asset Upload (非同步) → 批量上傳圖片
✅ Export (非同步) → 批量匯出
✅ Resize → 批量尺寸調整
✅ Merge → 合併設計
✅ Webhook → 監聽設計變更

## 上傳限制

- 圖片：< 50 MB (JPEG/PNG/HEIC/GIF/TIFF/WEBP)
- 影片：< 500 MB (M4V/MKV/MP4/MPEG/QuickTime/WebM)

## 建議整合路徑

Hybrid: MCP Plugin (文件查詢) + Hermes Skill (REST API 操作) + 共用 token 管理。
