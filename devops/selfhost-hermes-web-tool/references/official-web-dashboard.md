# Hermes Agent 官方 Web Dashboard

> 注意：這是 Hermes Agent **內建**的 `hermes dashboard` 功能，  
> 與本技能部署的第三方 GitHub 自託管工具是**不同的東西**。

## 快速識別

| 特性 | 官方 Built-in Dashboard | 第三方自託管工具 |
|------|------------------------|------------------|
| 啟動方式 | `hermes dashboard` | `node server.js` 等 |
| 原始碼 | Hermes Agent 專案內 | GitHub 上獨立專案 |
| 功能定位 | Hermes 完整管理後台 | 特定監控/管理工具 |
| 認證 | Username/Password, OAuth, OIDC | 取決於各專案 |
| Port 預設 | 9119 | 各專案自訂 |

## 安裝

```bash
cd ~/.hermes/hermes-agent && uv pip install -e ".[web,pty]"
# 或整包安裝: uv pip install -e ".[all]"
```

## 啟動

```bash
hermes dashboard                    # localhost:9119
hermes dashboard --host 0.0.0.0     # 所有網路介面
hermes dashboard --port 8080        # 自訂 port
hermes dashboard --no-open          # 不自動開瀏覽器
```

## 15 個管理頁面

| 頁面 | 功能 |
|------|------|
| **Status** | Agent 版本、Gateway 狀態、近期對話 |
| **Chat** | 瀏覽器內嵌 TUI (xterm.js + WebGL) |
| **Config** | 150+ 設定欄位表單編輯 |
| **API Keys** | `.env` 金鑰管理 |
| **Sessions** | 對話歷史瀏覽/搜尋/匯出/刪除 |
| **Logs** | 日誌檢視與即時 tail |
| **Analytics** | Token 用量與成本分析 |
| **Cron** | 排程任務管理 |
| **Profiles** | Profile 建立與管理 |
| **Skills** | 技能啟用/停用/安裝 |
| **MCP** | MCP 伺服器管理 |
| **Webhooks** | Webhook 訂閱管理 |
| **Pairing** | Messaging 配對管理 |
| **Channels** | 20+ 通訊平台連線 |
| **System** | 主機統計/更新/診斷/備份 |

## 認證機制（非 loopback 綁定時自動啟用）

| Provider | 適合場景 |
|----------|----------|
| Username/Password (`basic`) | 內網/VPN/自託管 |
| Nous Portal OAuth (`nous`) | 公開網路（推薦） |
| Self-hosted OIDC | 自建 OIDC (Keycloak/Auth0) |

⚠️ `--insecure` 會完全關閉認證，不建議用於遠端連線。

## REST API

所有 `/api/*` 端點均可透過 `?profile=<name>` 指定 profile。

| Method | Path | 用途 |
|--------|------|------|
| GET | `/api/status` | Agent 版本、Gateway 狀態 |
| GET | `/api/sessions` | 最近對話列表 |
| GET/PUT | `/api/config` | 讀寫設定 |
| GET/PUT/DELETE | `/api/env` | 管理環境變數 |
| GET | `/api/sessions/{id}/messages` | 完整對話歷史 |
| GET | `/api/logs` | 日誌 |
| GET | `/api/analytics/usage` | 分析 |
| GET/POST/PUT/DELETE | `/api/cron/jobs` | Cron 管理 |
| POST | `/api/gateway/start\|stop\|restart` | Gateway 生命週期 |

## 與 Hermes Desktop 遠端連線

1. 遠端主機執行 `hermes dashboard --host 0.0.0.0 --no-open`
2. 設定 Username/Password 或 OAuth
3. Desktop → Settings → Gateway → Remote gateway → 輸入 `http://VM_IP:9119`

## 與 Open WebUI 的差異

- **Web Dashboard** (port 9119) = Hermes 管理後台
- **API Server** (port 8642) = OpenAI 相容 endpoint，供 Open WebUI 等前端使用
- 兩者是不同東西，不要混淆

## 診斷

確認 gateway 狀態：
```bash
curl -s http://localhost:9119/api/status | jq '.auth_required, .auth_providers'
```

## 參考來源

完整文件：https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard
