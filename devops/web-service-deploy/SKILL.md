---
name: web-service-deploy
description: "Full lifecycle web service deployment: domain registration, DNS setup, nginx reverse-proxy, SSL certificate, and SPA frontend deployment."
version: 1.0.0
author: Hermes Agent
tags: [nginx, domain, ssl, deployment, dns, web-server]
---

# Web Service Deploy

End-to-end web service deployment: from buying a domain to serving a working HTTPS SPA with API backend on your own server.

## When to Use

- User bought a new domain and wants it pointing to this server.
- User needs to deploy a web dashboard/SPA with an API backend.
- Existing site needs SSL, domain changes, or routing fixes.
- **User says the site is down / returning errors — diagnostic rescue needed.**
- User says "買好了啊 你處理" after registering a domain.

## Troubleshooting: Site is Down (Rescue Diagnostic)

When a user reports a website is down or returning errors, **do not start proposing solutions or asking which server to fix**. Follow this diagnostic pipeline instead.

### Diagnostic Pipeline

```
Layer 1: DNS → Where is the domain pointing?
Layer 2: Server → Is that IP alive?
Layer 3: Web Server → Is nginx/Apache running?
Layer 4: Backend App → Is the proxied service alive?
Layer 5: Configuration → Is nginx routing correct?
```

### Layer 1 — DNS Check

```bash
# Check current A record
dig +short example.com
nslookup example.com 8.8.8.8

# Compare against known server IPs
# VM might have changed IP (old GCP e2-micro IP ≠ new VM IP)
# DNS provider might still point to dead IP
```

**Key insight: the DNS A record is the single source of truth for where traffic goes.** If it points to an old/dead IP, fixing the server won't help — the world can't reach it.

### Layer 2 — Server Reachability

```bash
curl -sI http://<IP>:80
curl -sI https://<IP>:443
# If port 22 is open but 80/443 is not → web server issue
# If all ports dead → server may be terminated or firewalled
```

### Layer 3 — Remote Server: Web Server Check

If SSH is available but the VM is in a different GCP project (different SSH keys may be needed):

```bash
# Try each SSH key; google_compute_engine works for GCP project-level keys
ssh -i ~/.ssh/google_compute_engine user@<IP> '
  ss -tlnp | grep -E ":(80|443) "
  systemctl is-active nginx
  cat /etc/nginx/sites-enabled/*
'
```

**SSH key priority for GCP VMs:**
| SSH Key | Use Case |
|---------|----------|
| `~/.ssh/google_compute_engine` | GCP project-level SSH keys (works across VMs in same project) |
| `~/.ssh/id_rsa` / `id_ed25519` | Custom keys, might not be authorized on the target VM |

### Layer 4 — Backend App Check

```bash
ssh -i ~/.ssh/google_compute_engine user@<IP> '
  # Is the app process alive?
  ps aux | grep -E "node|python|gunicorn|uvicorn" | grep -v grep

  # Is it listening on the expected port?
  ss -tlnp | grep <PORT>

  # Check app logs
  sudo journalctl -u <service-name> --no-pager -n 30
  sudo tail -50 /var/log/nginx/error.log
'
```

### Layer 5 — Configuration Check

```bash
ssh -i ~/.ssh/google_compute_engine user@<IP> '
  # Does nginx config proxy to the right port?
  cat /etc/nginx/sites-enabled/<domain>

  # Does the app actually handle the proxied path?
  # App may only have /health, /v1/* routes → root / returns 404
  curl -s http://127.0.0.1:<PORT>/health
  curl -sI http://127.0.0.1:<PORT>/
'
```

### Common Rescue Scenarios

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `connection refused` on port 80/443 | nginx not installed or stopped | Install/start nginx, configure site |
| `301` redirect works but `https` times out | SSL cert missing or expired | Get Let's Encrypt cert |
| HTTPS returns `404 Not Found` | Backend app has no route for `/` | Add landing page or redirect `/` to `/health` or a frontend |
| HTTPS returns `502 Bad Gateway` | Backend app down or wrong proxy port | Check app process, fix proxy_pass port |
| App logs show `401` | Missing or invalid upstream API keys | Check env vars / credential pool |
| nginx error log: `permission denied` | Socket file permissions | Check user/group of socket, add www-data to group |

### Applying the Fix on a Remote VM

If the server is reachable via SSH but needs nginx + SSL installed fresh:

```bash
# 1. SSH in
ssh -i ~/.ssh/google_compute_engine user@<IP>

# 2. Install nginx (if missing)
sudo apt update && sudo apt install -y nginx

# 3. Create nginx site config
sudo tee /etc/nginx/sites-available/<domain> << 'EOF'
server {
    listen 80;
    server_name <domain> www.<domain>;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name <domain> www.<domain>;
    ssl_certificate /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:<APP_PORT>;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 4. Enable site
sudo ln -sf /etc/nginx/sites-available/<domain> /etc/nginx/sites-enabled/

# 5. Get SSL cert
sudo nginx -s stop
sudo certbot certonly --standalone -d <domain> -d www.<domain> \
  --non-interactive --agree-tos --email user@example.com
sudo nginx

# 6. Verify
curl -sI http://<domain>/    # expect 301
curl -skI https://<domain>/  # expect 200
```

> **Important:** `certbot certonly --standalone` requires nginx to be **stopped** first (port 80 must be free). After cert is issued, restart nginx.

### Landing Page for API-Only Backends

If the backend is an API router (Express/FastAPI with only `/api/*` or `/v1/*` routes), the root `/` will return 404 by default. Fix with a minimal static landing page or redirect:

```nginx
# Option A: Simple redirect to health endpoint
location = / {
    return 302 /health;
}

# Option B: Static landing page
location / {
    root /var/www/landing;
    try_files $uri $uri/index.html =404;
}
```

Create a minimal `index.html` for Option B:
```html
<!DOCTYPE html><html lang="zh-TW">
<head><meta charset="UTF-8"><title>Service</title></head>
<body><h1>Service Running</h1><p>API endpoints available at /v1/</p></body>
</html>
```

## Prerequisites

- Server with public IP (check via `curl -s https://api.ipify.org`)
- Nginx installed (`sudo apt install nginx`)
- Certbot installed (`sudo apt install certbot`)
- Port 80 and 443 open in firewall (`sudo ufw allow 80/tcp && sudo ufw allow 443/tcp`)
- Domain registrar API key (if using API-based DNS management)

## Domain Registration

### Recommended Registrars
| Registrar | Pros | Link |
|-----------|------|------|
| **Porkbun** | Cheapest for most TLDs, good API | porkbun.com |
| **Cloudflare Registrar** | Cost-price, integrated DNS + CDN | dash.cloudflare.com |

### Check Domain Availability (via RDAP)
```bash
python3 -c "
import urllib.request, json
try:
    req = urllib.request.Request('https://rdap.verisign.com/com/v1/domain/example.com')
    resp = urllib.request.urlopen(req, timeout=10)
    print('已被注册')
except urllib.error.HTTPError as e:
    if e.code == 404:
        print('可注册！')
"
```

## DNS Configuration via Porkbun API

### Enable API Access
1. Log into Porkbun, Account, API Access
2. Enable API access for the specific domain (or all domains)

### DNS Management Script Pattern
```python
API_KEY = "pk1_..."
SECRET_KEY = "sk1_..."
BASE = "https://api.porkbun.com/api/json/v3"
DOMAIN = "example.com"
SERVER_IP = "1.2.3.4"

def api_call(endpoint, data=None):
    payload = {"apikey": API_KEY, "secretapikey": SECRET_KEY}
    if data: payload.update(data)
    req = urllib.request.Request(f"{BASE}/{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

# 1. List existing records
r = api_call(f"dns/retrieve/{DOMAIN}")

# 2. Delete parking records (ALIAS, wildcard CNAME)
api_call(f"dns/delete/{DOMAIN}/{record_id}")

# 3. Add A record
api_call(f"dns/create/{DOMAIN}", {
    "name": "", "type": "A", "content": SERVER_IP, "ttl": 300
})

# 4. Add www CNAME
api_call(f"dns/create/{DOMAIN}", {
    "name": "www", "type": "CNAME", "content": f"{DOMAIN}.", "ttl": 300
})
```

> **注意 conflict 错误：** 如果已有 ALIAS 记录指向 parking page，直接加 A record 会回传 conflict。必须先删除 ALIAS 和 wildcard CNAME 后才能建立 A record。

## Nginx Configuration

### Basic SPA + API Proxy Pattern
```nginx
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    root /var/www/brand-site;

    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # SPA assets (use ^~ to beat regex)
    location ^~ /assets/ {
        alias /var/www/brand-site/m/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # SPA index.html
    location /m/ {
        alias /var/www/brand-site/m/;
        try_files $uri $uri/ /m/index.html;
    }

    # Static site fallback
    location / {
        try_files $uri $uri.dc.html $uri/ =404;
    }
}
```

> **^~ /assets/ 的用途：** nginx 的 regex location (`~* .(js|css|png)$`) 优先于 prefix location (`/assets/`)。如果有一条 `.(js|css)$ { try_files $uri =404 }` 的 regex，它会比 `/assets/` prefix 先匹配到 JS/CSS。使用 `^~` 修饰符让 prefix 绕过 regex，确保 assets 走 alias 路径而不是 root。

## SSL Certificate (Let's Encrypt)

### Get Certificate
```bash
sudo nginx -s stop
sudo certbot certonly --standalone -d example.com -d www.example.com \
  --non-interactive --agree-tos --email you@example.com
sudo nginx
```

### Firewall
```bash
sudo ufw allow 443/tcp
```

## Verification Checklist

```bash
# 1. HTTP to HTTPS redirect
curl -s -o /dev/null -w "%{http_code} to %{redirect_url}" http://example.com/
# Expect: 301 to https://example.com/

# 2. HTTPS
curl -sk -o /dev/null -w "%{http_code}" https://example.com/
# Expect: 200

# 3. API
curl -sk https://example.com/api/status | head -c 100

# 4. Static assets
JS=$(curl -sk https://example.com/m/ | grep -oP '/assets/index-[^.]+\.js')
curl -sk -o /dev/null -w "%{http_code} (%{size_download}B)" "https://example.com$JS"

# 5. DNS propagation
nslookup example.com 8.8.8.8
```

## Security First

Before making any service publicly accessible, **always confirm with the user** whether they want authentication. Even if the user says "你處理" (handle it), do NOT expose dashboards, admin panels, or API backends without password protection unless the user explicitly says it's OK to be public.

**Default policy:** internal tools → password required. Ask before exposing.

## Pitfalls

### Old process holds the port
After updating server code (server.py, nginx config), the old process may still hold the port. The new process silently fails.

**Fix:** kill the old process before starting the new one:
```bash
ss -tlnp | grep 8001       # find PID
sudo kill <PID>              # kill old
# then start new
```

### Regex location wins over prefix in nginx
Nginx processes regex locations (`~*`) before prefix even when the prefix is listed first. For `/assets/` serving from a non-root directory, you MUST use `^~ /assets/` to skip regex matching.

### Sub-path API proxy must be declared before the SPA fallback
When API routes live under the same URL prefix as the SPA（e.g. `/m/api/` under `/m/`）, the API proxy location block MUST appear before the SPA `try_files` block. Otherwise nginx matches the shorter SPA prefix first and returns `index.html` (HTTP 200 with HTML body) instead of proxying to the backend. The browser's `fetch()` gets HTML instead of JSON, resulting in parse errors that appear as 404 or "Unexpected token <".

```nginx
# ✅ CORRECT: longer API prefix before shorter SPA fallback
location /m/api/ {
    rewrite ^/m/api/(.*) /api/$1 break;
    proxy_pass http://127.0.0.1:8082;
    ...
}
location /m/ {
    alias /var/www/brand-site/m/;
    try_files $uri $uri/ /m/index.html;  # SPA fallback last
}

# ❌ WRONG: shorter prefix catches /m/api/* first → returns index.html
location /m/ { ... }     # catches everything including /m/api/*
location /m/api/ { ... } # never reached
```

### **`openssl passwd` generates htpasswd-incompatible hashes:**
If you create a password file with `openssl passwd -apr1`, the resulting hash format is rejected by nginx — all auth requests return 401 even with the correct password.
**Fix:** always use `htpasswd -c -i` to create password files.

### Dream dashboards with mock data
When building a React dashboard with a "dream" mockup page for visual design, NEVER make it the default route. The mock data will show instead of real API data when deployed to production. The default route must point to a real-data page (e.g. API status, keys list).

**Fix:** Check AppRouter for `useState(ROUTES.DREAM)` and change to `ROUTES.API_STATUS`.

### FreeLLM container key updates
FreeLLM stores upstream API keys encrypted in a SQLite DB. To update a key:
1. Encrypt the new key using the container's Node.js
2. Update the DB with sudo sqlite3
3. Restart the container

### Directory permissions block DB access
The Mini App server runs as a non-root user but the FreeLLM DB is at `/var/lib/docker/volumes/` where intermediate directories are root-only.
```bash
sudo chmod +rx /var/lib/docker/
sudo chmod +rx /var/lib/docker/volumes/
sudo chmod 644 /var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db
```

### API backend with no root route returns 404 on `/`
When proxying to a backend that only serves API endpoints (`/health`, `/v1/*`, `/api/*`), the root path `/` returns a generic 404 from the framework (Express, FastAPI, etc.). This looks broken to anyone visiting the domain in a browser.

**Detect:**
```bash
curl -skI https://<domain>/
# Look for: HTTP/1.1 404 Not Found + X-Powered-By: Express
```

**Fix options:**
- Add a `location = / { return 302 /health; }` block in nginx
- Or serve a minimal static landing page from nginx root
- Or configure the backend app to handle `/` (e.g., redirect to docs)

### Let's Encrypt on a remote VM: nginx must be stopped
When running `certbot certonly --standalone` on a remote VM via SSH, nginx must be fully stopped (not just `nginx -s quit`). Use `sudo nginx -s stop` or `sudo systemctl stop nginx`. If certbot says port 80 is in use, check with `sudo ss -tlnp | grep :80` and kill the holding process.

## References

- `nginx-spa-basic-auth` — Auth-protected SPA deployment (covers ^~ /assets/, Cloudflare cache pitfalls in more depth)
- `hermes-custom-providers` — LLM provider key management, credential pool, env var key storage
