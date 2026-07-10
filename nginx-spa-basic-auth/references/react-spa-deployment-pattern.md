# React SPA + Python Backend — Nginx 部署模式

> 實戰案例：Hermes Proxy Console（2026-07-09）
> 場景：React Vite SPA + Python 單檔 HTTP 後端 + JWT 自訂登入

## 拓撲

```
使用者瀏覽器 → :443 → nginx
  ├── /api/*       → proxy_pass Python 後端 (:8081)
  ├── /m/          → alias /var/www/brand-site/m/ (React SPA)
  └── /assets/*    → alias /var/www/brand-site/m/assets/ (JS/CSS)
```

## Nginx 配置關鍵點

### 1. Assets 路徑衝突：`^~` vs `~*` 優先級

React Vite build 產出 `index.html` 引用 `/assets/index-xxxxx.js`（絕對路徑）。

nginx regex location `~* \.(js|css|png|...)$` 會**優先於** prefix location `/assets/` 被匹配，導致 `try_files` 從錯誤的 root 路徑尋找。

**解法：** 使用 `^~` 修飾詞，讓 prefix location 強制優先於 regex：

```nginx
location ^~ /assets/ {
    alias /var/www/brand-site/m/assets/;
    expires 30d;
}
```

### 2. SPA fallback：所有路徑回傳 index.html

```nginx
location /m/ {
    alias /var/www/brand-site/m/;
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
    try_files $uri $uri/ /m/index.html;
}
```

### 3. API proxy：避免覆蓋現有端點

React SPA 所有 API 呼叫走 `/api/*`。但伺服器可能已有 `/api/ai/`（FreeLLM）和 `/api/legal/`（zhiyan-legal）等更特定 location。

nginx 會先匹配最特定的 prefix，所以 `/api/ai/` 優先於 `/api/`：

```nginx
location /api/ai/   { proxy_pass http://127.0.0.1:3001; }  # 優先
location /api/legal/ { proxy_pass http://127.0.0.1:8001; }  # 優先
location /api/      { proxy_pass http://127.0.0.1:8081; }  # 通用後備
```

### 4. HTTPS 強制轉跳

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
```

## 自訂登入系統

### 前端：獨立 login.html（不經過 React）

建立獨立的 `login.html` 放在 SPA 目錄下，不經過 React 路由：

```
/var/www/brand-site/m/
  ├── index.html    ← React SPA
  └── login.html    ← 登入頁面（純 HTML/CSS/JS）
```

登入流程：
1. React App (`index.html`) mount 時檢查 `localStorage.getItem('token')`
2. 無 token → `window.location.href = '/m/login.html'`
3. login.html 用 `fetch('/api/auth/login', { method: 'POST', body: JSON.stringify({password}) })`
4. 成功 → `localStorage.setItem('token', data.token)` → `window.location.href = '/m/'`
5. 失敗 → 顯示錯誤訊息

### 後端：JWT token

Python 後端實作 HMAC-SHA256 token：

```python
import hmac, hashlib, base64, time

SECRET = "32-byte-random-hex"  # 存 ~/.hermes/env/.auth_secret
TOKEN_TTL = 86400  # 24h

def _generate_token(user_id="admin"):
    expiry = int(time.time()) + TOKEN_TTL
    payload = f"{user_id}:{expiry}"
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode().rstrip("=")
    return token

def _verify_token(token):
    padded = token + "=" * (4 - len(token) % 4)
    decoded = base64.urlsafe_b64decode(padded).decode()
    payload, sig = decoded.rsplit(":", 1)
    expected = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    user_id, expiry = payload.split(":", 1)
    if int(expiry) < time.time():
        return None
    return user_id
```

### 密碼驗證：bcrypt

```python
import bcrypt

# 建立 hash（一次性）
hash = bcrypt.hashpw(b"my_password", bcrypt.gensalt())
with open("~/.hermes/env/.auth_password", "w") as f:
    f.write(hash.decode())

# 驗證
def verify_password(password):
    with open("~/.hermes/env/.auth_password") as f:
        stored = f.read().strip()
    return bcrypt.checkpw(password.encode(), stored.encode())
```

### Rate limiting

```python
_LOGIN_ATTEMPTS = {}  # ip -> [attempts, window_start]

def check_rate_limit(ip):
    now = time.time()
    if ip in _LOGIN_ATTEMPTS:
        a, w = _LOGIN_ATTEMPTS[ip]
        if now - w < 60:
            if a >= 5:
                return False  # 429
            _LOGIN_ATTEMPTS[ip][0] += 1
        else:
            _LOGIN_ATTEMPTS[ip] = [1, now]
    else:
        _LOGIN_ATTEMPTS[ip] = [1, now]
    return True
```

## systemd 自動重啟

建立 `/etc/systemd/system/hermes-miniapp.service`：

```ini
[Unit]
Description=Hermes Mini App Backend
After=network.target

[Service]
Type=simple
User=ysga1
Group=ysga1
ExecStart=/usr/bin/python3 /usr/local/bin/miniapp-server.py 8081
WorkingDirectory=/home/ysga1
Restart=always
RestartSec=5
Environment=HOME=/home/ysga1
Environment=USER=ysga1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable hermes-miniapp
sudo systemctl restart hermes-miniapp
```

## 金鑰安全：只放 env，不放 config

| 檔案类型 | 可以放 key？ | 說明 |
|:---------|:------------:|:------|
| `.env` | ✅ | `echo 'KEY=val' >> ~/.hermes/.env` |
| `auth.json` | ✅ | Hermes credential pool，read_file 會擋 |
| `systemd env.conf` | ✅ | 僅啟動時載入 |
| `config.yaml` | ❌ | read_file 可讀，git 可能被推 |
| `mem0.json` | ❌ | 第三方 JSON，用 `_FROM_ENV_` 佔位符 |

## 完整檔案結構

```
/var/www/brand-site/m/
  index.html          ← React SPA
  login.html          ← 登入頁
  assets/             ← Vite build output
    index-xxxxx.js
    index-xxxxx.css
    PageName-xxxxx.js (lazy loaded chunks)

/usr/local/bin/
  miniapp-server.py   ← Python 後端（含 JWT auth、key mgmt、API）

/etc/systemd/system/
  hermes-miniapp.service  ← systemd unit

~/.hermes/env/
  .auth_password      ← bcrypt hash
  .auth_secret        ← HMAC signing key
  keys-registry.json  ← API keys metadata
```

## 已知陷阱

- `^~ /assets/` 很重要！沒有它 nginx regex 會吃掉 JS/CSS 請求
- login.html 的權限必須 `644`（`chown www-data:www-data`），否則 nginx 回傳 403
- React build 後 JS 檔案 hash 會變，但 nginx 端不需重啟（hash 在 HTML 裡）
- Password hash 用 `htpasswd` 產生，不要用 `openssl passwd`（格式不相容）
- 後端重新部署：殺掉舊行程後等 3 秒確認 port 已釋放，再啟新行程
- `sudo pkill -f` 可能殺到 gateway 本身（共用 Python 行程），改用 `kill <PID>`
