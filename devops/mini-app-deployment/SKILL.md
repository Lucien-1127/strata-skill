---
name: mini-app-deployment
description: Hermes Proxy Console Mini App 的完整部署工作流 — build → deploy → verify → restart
version: 1.0.0
category: devops
tags:
  - deployment
  - mini-app
  - react
  - nginx
  - verification
triggers:
  - 修改 Mini App 前端原始碼（React/TSX）
  - 部署 Mini App 到 lucien126.com/m/
  - 報告「Mini App 修好了」之前強制執行
---

# Mini App 部署工作流

## ⚠️ 核心教訓（2026-07-09）

**改了 code ≠ 部署了。build 成功 ≠ 用戶看得到。**

老闆連續 3 次說「根本沒有更新啊」、「你又在騙我了」。
根因：改了 AppRouter.tsx 原始碼但從未執行 `npm run build` + `cp` 部署。
grep deployed JS 發現新功能（底部導覽列）不存在 → 證明部署從未發生。

**鐵則：每次前端變更後，必須跑完以下 5 步才能說「已部署」。**

---

## 部署 5 步驟（全部必須執行）

### Step 1: Build

```bash
# v2 新版前端
cd /home/ysga1/hermes-miniapp/frontend
# v1 舊版前端
# cd /home/ysga1/hermes-proxy-console
npm run build
```

檢查：`exit 0` + no TypeScript errors + no ESLint errors

> **Vite 6 + rolldown 注意：** 新版 Vite 使用 rolldown（Rust bundler），搭配 `verbatimModuleSyntax: true` 時，type-only export（`export interface`）在 consuming files 必須使用 `import type` 匯入，否則 build 會報 `MISSING_EXPORT`。例：
> ```ts
> // api.ts
> export interface ModelSummary { ... }    // type-only export
> // DashboardPage.tsx
> import type { ModelSummary } from "./api";  // ✅
> import { ModelSummary } from "./api";       // ❌ MISSING_EXPORT
> ```

### Step 2.5: 深色主題驗證（TG 變數洩漏檢查）

**TG WebView 不保證注入 `--tg-theme-*` CSS 變數**。若原始碼中有 `var(--tg-theme-*, #fff)` 殘留，用戶手機上會看到全白畫面。

```bash
# Build 前檢查（應回傳 0）
grep -r 'var(--tg-theme-' /home/ysga1/hermes-proxy-console/src/pages/ \
  /home/ysga1/hermes-proxy-console/src/components/layout/ \
  /home/ysga1/hermes-proxy-console/src/app/router/ \
  /home/ysga1/hermes-proxy-console/src/styles/ 2>/dev/null | wc -l
```

若 > 0 → 執行全域替換（見 `hermes-proxy-console` Pitfall > TG WebView CSS 變數）。

部署後可在瀏覽器 console 確認：
```js
getComputedStyle(document.body).background  // 應為 rgb(15, 23, 42) = #0f172a
```

### Step 3: Deploy to nginx 目錄

```bash
sudo rm -rf /var/www/brand-site/m/assets/*
sudo cp -r dist/* /var/www/brand-site/m/
sudo chown -R www-data:www-data /var/www/brand-site/m/
```

### Step 4: 驗證部署的 JS 包含新功能

```bash
# 找出最新部署的主 JS bundle
BUNDLE=$(ls -t /var/www/brand-site/m/assets/index-*.js | head -1)
# 確認新功能關鍵字存在
grep -c '新功能關鍵字' "$BUNDLE"
```

如果回傳 0 → 部署失敗，回到 Step 1

### Step 5: 驗證 HTTPS 端點回傳新版

```bash
# 確認 HTML 引用正確的 JS bundle（v2 路徑為 /m/assets/）
curl -sk https://lucien126.com/m/ | grep 'src="/m/assets/'

# 確認 API health
curl -sk https://lucien126.com/m/api/health
# 應回: {"ok":true,"version":"2.0.0"}

# 確認登入可用
curl -sk -X POST https://lucien126.com/m/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"Ting7809"}'
# 應回 token

# 確認 dashboard 需 auth（回 UNAUTHORIZED = API 正常）
curl -sk https://lucien126.com/m/api/dashboard
```

### Step 5: 通知用戶

**在告訴用戶「修好了」之前，以上 4 步全部通過。**
建議用戶開無痕視窗測試（繞過 Telegram WebView 快取）。

---

## 路徑速查

| 項目 | 路徑 |
|:------|:------|
| React 原始碼 (v2 新版) | `/home/ysga1/hermes-miniapp/frontend/` |
| React 原始碼 (v1 舊版) | `/home/ysga1/hermes-proxy-console/` |
| Build 輸出 | `<project>/dist/` |
| Nginx 部署目錄 | `/var/www/brand-site/m/` |
| 後端伺服器 (v2 FastAPI) | `/home/ysga1/hermes-miniapp/backend/main.py` |
| 後端伺服器 (v1 舊版) | `/usr/local/bin/miniapp-server.py`（已退役） |
| HTTPS 端點 | `https://lucien126.com/m/` |
| API 端點 (v2) | `https://lucien126.com/m/api/...` |
| API 端點 (v1 舊版) | `https://lucien126.com/api/...` |
| systemd 服務名 | `hermes-miniapp`（監聽 port 8082） |
| 後端 data 目錄 | `/home/ysga1/hermes-miniapp/data/` |
| 後端 venv | `/home/ysga1/hermes-miniapp/backend/venv/` |

---

## 伺服器管理

### 重啟後端（systemd）

```bash
sudo systemctl restart hermes-miniapp
sudo systemctl status hermes-miniapp --no-pager
```

### 重啟 nginx（非 systemd）

```bash
# nginx 為直接啟動的 master process（非 systemd 管理）
# reload 必須用 signal，不能用 systemctl
sudo kill -HUP $(cat /run/nginx.pid 2>/dev/null || pgrep -f "nginx: master")
# 或
sudo nginx -s reload
```

### 啟動順序

1. `sudo systemctl start hermes-miniapp`（後端先起來）
2. 確認 `curl -sk https://lucien126.com/m/api/health` 回 `{"ok":true}`
3. 再部署前端靜態檔案

---

## 常見失敗模式

| 錯誤 | 根因 | 解法 |
|:------|:------|:------|
| 老闆說「沒更新」 | 只改了 code 沒 build+deploy | 跑完整 5 步驟 |
| JS 404 | nginx 路徑或權限錯誤 | 檢查 `/etc/nginx/sites-available/brand-site` |
| API 401 | Token 過期或格式錯誤 | 重新登入取得新 token |
| Telegram WebView 顯示舊版 | WebView 快取 | 用戶開無痕 / 清除 Telegram 快取 |
| miniapp-server 死掉 | silent crash | `sudo systemctl restart hermes-miniapp` |
| `systemctl reload nginx` → "not active" | nginx 非 systemd 啟動（直接 `nginx` 命令） | 改用 `sudo nginx -s reload` |
| 底部導覽列被內容蓋住 / 有奇怪空白 | PageContainer 有 100px 底部 padding（舊設計無導覽列時遺留） | 改為 `80px` 或更小 |
| 刪除頁面後 build 報 TS6133 unused | 舊頁面引用的 hook/state 還在 AppRouter 裡 | 移除不再使用的 import / hook / function |
| **🔴 全白畫面（用戶說「白色的頭白色的底 很醜」）** | TG WebView 不注入 `--tg-theme-*` CSS 變數，全部 fallback 到 `#fff` | Build 前跑 Step 2.5 檢查 + sed 全域替換為硬編碼深色值 |
| **API fetch 404（curl 正常但瀏覽器失敗）** | nginx location `/m/api/` 未放在 `/m/` 之前，被 SPA fallback 攔截 | 確認 `/m/api/` location block 出現在 `/m/` block 之前 |
| **🔴 POST API 回 405（curl 正常但瀏覽器 fail）** | `rewrite ^/m/api/(.*) /api/$1 break;` + `proxy_pass http://...:port;`（無 URI）會導致 POST body 遺失，瀏覽器 preflight 或 POST 變 405 | 改用 `proxy_pass http://127.0.0.1:8082/api/;`（**含 trailing `/api/`**，刪除 rewrite 指令）。原理：`proxy_pass` 含 URI 時，nginx 會將 matched location prefix `/m/api/` 替換為 `/api/`，無需 rewrite |
| **Vite build `MISSING_EXPORT`** | Vite 6 rolldown + `verbatimModuleSyntax: true` 不認 type-only export | 用 `import type { X }` 匯入 type-only 的 interface/type |
| **🔴 401 無限迴圈（登入頁永不顯示）** | 兩個可能原因：(a) 舊 token 殘留 localStorage → App `loggedIn=true` → Dashboard render → API 401 → `clearToken()` 但 React state 未更新 → 無限重試；(b) **FastAPI `detail` 包裝格式**：後端回 `{"detail": {"error": {...}}}` 但前端查 `json.error?.code` → 永遠 undefined → `clearToken()` 永不觸發。偵錯：`sudo grep "42.79.35.124" /var/log/nginx/access.log | tail -15` → 若只有 GET dashboard 401 而無 login POST = auth loop | 見 `references/react-auth-expiry-pattern.md`：加 `auth-expired` event + 同時檢查 `json.detail?.error?.code` 和 `json.error?.code` |
| **🔴 登入成功後全白畫面（後端 200 OK 但前端空白）** | `new URL(bareHostname)` crash — 後端回傳 hostname 如 `api.cerebras.com`（缺 `https://`），前端 `new URL("api.cerebras.com")` 拋 `TypeError`，React 渲染崩潰。**手機上尤其無聲無息**（無 console，無 error dialog，就是全白）。偵錯：`curl` dashboard API 檢查每個欄位是否為合法 URL | 見 `references/react-blank-page-debug.md`：safeHostname wrapper + ErrorBoundary |

## 參考文件

- `references/react-router-slimdown.md` — React Router 瘦身：審計→簡化→清理→驗證打包 5 步驟
- `references/fastapi-backend-arch.md` — v2 後端架構筆記：JWT + bcrypt + SQLite 單檔案 FastAPI 模式，含啟動、systemd、API 合約細節
- `references/data-migration-freellm.md` — FreeLLM Docker SQLite → Miniapp SQLite 遷移步驟與陷阱（requests.model_id 為字串非 DB id）
- `references/react-auth-expiry-pattern.md` — React SPA 401 auth loop 修復：`auth-expired` 事件驅動登出
- `references/react-blank-page-debug.md` — 🔴 登入成功但全白：`new URL()` crash 偵錯 + safeHostname + ErrorBoundary 雙層防護

---

## 相關技能

- `iron-laws` — H1/H3：不可幻覺（聲稱修好但沒部署 = 幻覺）
- `user-communication-style` — §15 信任修復模式、§4b 用戶端驗證缺口
