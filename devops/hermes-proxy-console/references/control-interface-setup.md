# Hermes Control Interface — 第三方儀表板整合

## 概述

[xaspx/hermes-control-interface](https://github.com/xaspx/hermes-control-interface) (MIT, 793★) 是自託管的 Hermes Agent 網頁儀表板。
提供 12 個管理頁面：Home / Chat / Agents / Office / Monitor / Usage / Logs / Skills / Files / MCP / Maintenance。

## 安裝步驟

### 1. 安裝 Node 20+（系統 Node 18 不夠）

```bash
# 安裝 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 安裝 Node 20
nvm install 20
nvm use 20
```

### 2. Clone + 安裝依賴

```bash
git clone --depth=1 https://github.com/xaspx/hermes-control-interface.git
cd hermes-control-interface
npm install
```

### 3. 設定環境變數

```bash
cp .env.example .env
```
編輯 `.env`，設定：
- `HERMES_CONTROL_PASSWORD=<隨機密碼>`
- `HERMES_CONTROL_SECRET=<隨機 HMAC secret>`
- `HERMES_HOME=/home/<user>/.hermes`

### 4. Build + 啟動

```bash
npm run build
export PORT=10274
export HOST=0.0.0.0
node server.js
```

### 5. nginx 代理

在既有 server block 中加入：

```nginx
location /hci/ {
    proxy_pass http://127.0.0.1:10274/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

## 繁體中文翻譯

HCI 內建 i18n 系統，支援語系檔位於 `src/public/i18n/` 與 `dist/i18n/`。

### 加入繁體中文

1. 從 `en.json` 取得完整鍵值結構（433 個翻譯鍵）
2. 建立 `zh-TW.json`，翻譯所有鍵值
3. 修改 `dist/assets/index-*.js`，在支援語系陣列中加入 `zh-TW`：
   ```js
   // 搜尋 Bl=[`en`,`ja`] 改為
   Bl=[`en`,`ja`,`zh-TW`]
   ```
4. 同時處理瀏覽器語系偵測：在 `navigator.language.startsWith('ja')` 附近加入
   ```js
   (e.startsWith('zh')||e.startsWith('zh-'))?`zh-TW`
   ```
5. 重啟 service 生效

### 檔案位置

| 路徑 | 用途 |
|------|------|
| `src/public/i18n/zh-TW.json` | 原始碼（下次 build 時複製到 dist） |
| `dist/i18n/zh-TW.json` | 運行時載入 |
| `dist/assets/index-*.js` | 語系支援陣列 + 偵測邏輯（手動修改） |

## 已知限制

- 需要 Node >= 20（系統預設 Node 18 不夠）
- WebSocket 依賴 proxy_set_header Connection "upgrade"
- 登入後依 session cookie 維持認證
- Cloudflare 快取可能阻擋即時更新 — 部署後需 Purge Everything

## nvm 後續注意

每次啟動需先 `nvm use 20`。建議建立 systemd service 或直接在啟動腳本中 export NVM_DIR + source nvm.sh。
