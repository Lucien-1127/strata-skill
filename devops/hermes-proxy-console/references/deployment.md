# Hermes Proxy Console — 部署與 Nginx 整合

## 前提條件

- Vite build 產出在 `~/hermes-proxy-console/dist/`
- 靜態目錄假設為 `/var/www/brand-site/m/`（更改路徑需同步 nginx config）
- Python 後端（miniapp-server.py）從 `STATIC_DIR` 服務靜態檔案

## Build 與部署

```bash
cd ~/hermes-proxy-console && npm run build
sudo cp -r dist/* /var/www/brand-site/m/
sudo cp -r dist/* /var/www/brand-site/tg-app/   # Python 後端使用的路徑
sudo systemctl reload nginx
```

## Nginx SPA 配置

Telegram Mini App 使用 in-memory routing（或 hash-based routing），不需完整 SPA fallback 即可運作。但若未來加入 URL-based routing，需加上 `try_files $uri /m/index.html`：

```nginx
location /m/ {
    alias /var/www/brand-site/m/;
    # SPA fallback: 未知路徑一律回 index.html
    try_files $uri $uri/index.html /m/index.html;
    expires epoch;
    add_header Cache-Control "no-cache, no-store, must-revalidate, proxy-revalidate";
    add_header Pragma "no-cache";
}
```

**已知限制**：
- `alias` 與 `root` 的 `try_files` 路徑解析不同。使用 `alias` 時，`try_files` 最後一個 fallback 參數（如 `/m/index.html`）是相對於 document root，不是 alias 目錄。
- 複數 `location /m/` 區塊會導致 nginx 啟動失敗 — 每個路徑只能有一個 location。

## Python 後端 SPA 支援

`SimpleHTTPRequestHandler` 預設只服務存在的檔案。需手動加入 SPA fallback：

```python
def do_GET(self):
    path = urlparse(self.path).path
    if path == "/api/status":   self._json(self._get_dash_status())
    elif path.startswith("/api/"):
        self._json({"error":"unknown api"}, 404)
    else:
        serve_path = path.lstrip("/")
        full = os.path.join(STATIC_DIR, serve_path) if serve_path else STATIC_DIR
        if os.path.isfile(full):
            super().do_GET()
        else:
            self.path = "/index.html"
            super().do_GET()
```

## Cloudflare 快取問題診斷與處理

### 症狀

即使 nginx 設定了 `Cache-Control: no-cache, no-store` 和 `expires epoch`，Cloudflare 仍可能服務舊版 HTML。典型症狀：

| 測試方式 | 結果 |
|---|---|
| 本機測試：`curl -H "Host: zhiyan.dev" http://localhost/m/` | ✅ 回傳新內容 |
| 透過 CF：`curl https://zhiyan.dev/m/` | ❌ 回傳舊內容 |
| 直接 IP：`curl -H "Host: zhiyan.dev" http://$EXTERNAL_IP/m/` | ✅ 回傳新內容 |

**⚠️ 最極端的案例：CF 可能服務與你完全不相干的網站內容。**
實測 `zhiyan.dev` 在 CF 快取未清除時，曾經顯示過一個中國 AI 聊天站「只言」（`<title>只言</title>`）的內容 — 該站主題、語言、研究方向都與網站負責人無關。這通常發生在：
- 網域曾由他人持有，CF 快取了前持有人站的內容
- CF DNS 記錄指向變更後，邊緣未及時更新

### 診斷步驟

1. **檢查回應標頭**：
   ```bash
   curl -skI https://zhiyan.dev/m/ | grep -i "cf-cache\|cache-control"
   ```
   - `cf-cache-status: DYNAMIC` — CF 視為動態內容，但仍可能服務舊版
   - `cache-control: public, max-age=0` — 可能是舊頁面的標頭，非最新 nginx 設定

2. **檢查 cloudflared 隧道狀態**：
   ```bash
   ps aux | grep cloudflared | grep -v grep
   ```
   確認隧道已連線。若隧道已中斷，CF 無法連回 nginx，可能服務邊緣快取。

3. **檢查 nginx 本地回應**（bypass CF）：
   ```bash
   curl -sk -H "Host: zhiyan.dev" http://localhost/m/ | head -3
   ```
   這測試 nginx 本身是否正確。

4. **檢查外部 IP 直連**（bypass CF + tunnel）：
   ```bash
   EXTERNAL_IP=$(curl -s ifconfig.me)
   curl -sk -H "Host: zhiyan.dev" "http://$EXTERNAL_IP/m/" | head -3
   ```

### 解決方案

| 方法 | 說明 | 適合場景 |
|---|---|---|
| **Cloudflare API 清除快取** | `DELETE /client/v4/zones/:zone_id/purge_cache` | 有 API Token 時最快 |
| **Cloudflare 開發模式** | Dashboard → 啟用 Development Mode（bypass 3h） | 有 Dashboard 權限時 |
| **TryCloudflare 隧道** | `cloudflared tunnel --url http://localhost:8081` | 繞過 CF 快取的捷徑 |
| **部署全新路徑** | 建立 nginx `/dash/` location（全新 URL） | 有時仍被 CF 根頁快取干擾 |
| **等待過期** | CF 動態快取最終會更新 | 無控制權時被動等待 |

### TryCloudflare 快速解法

用於快速驗證或暫時解決 CF 快取問題：

```bash
# 使用 skill 內附的腳本
skill_view(name='hermes-proxy-console', file_path='scripts/start-tunnel.py')
# 然後透過 terminal 在背景執行
python3 /home/ysga1/.hermes/skills/devops/hermes-proxy-console/scripts/start-tunnel.py
```

腳本啟動後會輸出 `✅ TUNNEL URL: https://xxx.trycloudflare.com` 並自動儲存到 `~/.hermes/env/miniapp-tunnel-url.txt`。

**⚠️ 限制**：trycloudflare URL 每次重啟隧道都會改變，無持久性。正式環境建議使用 named tunnel 或直接修復 CF 快取。

### 驗證修復

清除 CF 快取後：
```bash
curl -skI https://zhiyan.dev/m/ | grep -i "cf-cache\|cache-control"
# 應看到 no-cache, no-store；cf-cache-status 應為 BYPASS 或 DYNAMIC

curl -sk https://zhiyan.dev/m/ | head -3
# 應顯示 <!doctype html><html lang="zh-TW">...
```

## 檔案同步策略

Python 後端的 miniapp-server 服務 `STATIC_DIR`（`/var/www/brand-site/tg-app/`），nginx 服務 `/m/`。部署時兩個目錄都要複製：

```bash
sudo cp -r dist/* /var/www/brand-site/m/
sudo cp -r dist/* /var/www/brand-site/tg-app/
```
