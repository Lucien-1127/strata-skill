# Canva OAuth Callback — Nginx 端點範本

## 用途

在現有 nginx 伺服器上快速建立一個 Canva OAuth 授權回呼接收端點，無需額外伺服器或 ngrok。

## nginx 設定

在既有 server block 中加入以下 location：

```nginx
# ── Canva OAuth Callback ────────────────
location = /canva-callback {
    add_header Content-Type text/html;
    return 200 '<!DOCTYPE html><html><body style="font-family:sans-serif;padding:2em;background:#0f172a;color:#e2e8f0"><h2>✅ 授權成功</h2><p>請複製整個網址列內容貼給 Hermes</p><pre id="code" style="background:#1e293b;padding:1em;border-radius:8px;word-break:break-all;color:#22c55e"></pre><script>const url = window.location.href; document.getElementById("code").textContent = url;</script></body></html>';
}
```

## 驗證

```bash
curl -s -o /dev/null -w '%{http_code}' https://你的網域/canva-callback
# → 應回傳 200
```

## 流程

1. 在 Canva Developer Portal 建立 Connect API 整合
2. Redirect URI 填入 `https://你的網域/canva-callback`
3. 取得 Client ID + Client Secret
4. 產生 PKCE OAuth 授權 URL → 用戶點開授權
5. Canva 跳轉回 callback 頁面，URL 帶 `?code=xxx`
6. 用戶複製整條 URL → 貼回對話 → 取出 authorization_code
7. 交換 access_token + refresh_token → 存入 `~/.hermes/env/canva.env`
