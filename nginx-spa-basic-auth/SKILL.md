---
name: nginx-spa-basic-auth
description: Configure NGINX to serve a single-page application (SPA) behind basic authentication, with proper asset routing and proxy headers.
version: 1.0.0
author: Hermes Agent
tags: [nginx, web-server, basic-auth, spa, reverse-proxy]
---
# NGINX SPA Basic Auth Skill

This skill covers configuring NGINX to reverse-proxy a Single-Page Application (SPA) API while serving static assets, protected by HTTP Basic Authentication.

## When to Use

- You have an internal SPA API (e.g., FreeLLMAPI) running on localhost:port.
- You want to expose it via a friendly domain or subpath (e.g., `https://example.com/admin/`).
- You require basic authentication for the entire exposed path.
- The SPA serves static assets (JS, CSS, images) under a common path like `/assets/`.

## Prerequisites

- NGINX installed and running (`sudo apt-get install -y nginx` or equivalent).
- The backend service is reachable at `http://127.0.0.1:<port>/`.
- `htpasswd` utility available (usually from `apache2-utils` package).

## Configuration Steps

1. **Create or edit the site configuration**  
   Edit `/etc/nginx/sites-available/<site-name>` (commonly `default` or a custom file).

2. **Set up the auth-protected location for the SPA**  
   ```nginx
   location /admin/ {
       auth_basic "智研 Admin Area";
       auth_basic_user_file /etc/nginx/.htpasswd;
       sub_filter_once off;
       sub_filter 'href="/assets/"' 'href="/admin/assets/"';
       sub_filter 'src="/assets/"' 'src="/admin/assets/"';
       proxy_pass http://127.0.0.1:3001/;
       proxy_http_version 1.1;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 120s;
       proxy_send_timeout 30s;
   }
   ```

3. **Serve static assets with the same authentication**  
   ```nginx
   location /assets/ {
       auth_basic "智研 Admin Area";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://127.0.0.1:3001/assets/;
       proxy_http_version 1.1;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_read_timeout 120s;
       proxy_send_timeout 30s;
   }
   ```

4. **(Optional) Handle favicons**  

   For an admin-backend favicon (e.g., FreeLLMAPI):
   ```nginx
   location /admin/favicon.svg {
       auth_basic "智研 Admin Area";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://127.0.0.1:3001/favicon.svg;
       proxy_http_version 1.1;
   }
   ```

   For the root site `/favicon.ico` (browser auto-request), suppress the 404 with `empty_gif`:
   ```nginx
   location = /favicon.ico {
       log_not_found off;
       access_log off;
       empty_gif;
   }
   ```

5. **Create or update the password file**  
   ```bash
   # Interactive (prompts for password):
   sudo htpasswd -c /etc/nginx/.htpasswd <username>

   # Non-interactive (password from stdin, for scripts):
   echo "mypassword" | sudo htpasswd -c -i /etc/nginx/.htpasswd <username>

   # To update password for existing user:
   echo "newpassword" | sudo htpasswd -i /etc/nginx/.htpasswd <username>
   ```

   ⚠️ **Do NOT use `openssl passwd -apr1` to generate htpasswd entries** — the hash format it produces is incompatible with nginx's htpasswd parser and will cause all auth requests to return 401 even with the correct password.

6. **Test and reload NGINX**  
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Verification

- Visit `https://<your-domain>/admin/` in a browser.
- You should see a login prompt. After entering credentials, the SPA loads and its assets (JS/CSS) are fetched from `/assets/` without additional prompts.
- Use browser devtools Network tab to confirm requests to `/assets/*` return 200 and include the same `Authorization` header.

## Common Pitfalls

- **Missing proxy headers**: Omitting `proxy_set_header Host $host;` can cause the backend to generate incorrect URLs.
- **Trailing slash mismatch**: Ensure `proxy_pass` includes a trailing slash if the location does, or vice‑versa, to avoid double paths.
- **Asset 404**: If `/assets/` requests return 404, verify the `location /assets/` block is placed **before** any broader location that might capture it (e.g., a regex or `/` location).

  **🪤 Regex location priority trap**: nginx processes **regex** locations (`~* \.(js|css|png|…)$`) before **prefix** locations (`/assets/`) regardless of order. A regex like `location ~* \.(js|css|…)$ { try_files $uri =404; }` will match `/assets/index.js` first and try to serve it from the root docroot — even if a `/assets/` prefix block with `alias` to a different directory exists.

  **Fix**: use the `^~` prefix modifier on the assets location to bypass regex evaluation:
  ```nginx
  location ^~ /assets/ {
      alias /var/www/your-spa/m/assets/;
      expires 30d;
      add_header Cache-Control "public, immutable";
  }
  ```
  The `^~` tells nginx: "if this prefix matches, skip regex matching entirely." Without it, regex wins and your assets 404.

  **Symptom**: curl returns 404 on JS/CSS but 200 on HTML; static assets in subdirectory serve fine when accessed directly via their full path but fail via `GET /assets/index-xyz.js`.
- **Auth loops**: If you see repeated login prompts, check that the `auth_basic_user_file` path is correct and the file is readable by the NGINX worker process.
- **Static asset caching**: During development, you may need to bypass cache; add `add_header Cache-Control "no-store";` temporarily inside the `/assets/` block if needed.
- **`sub_filter_types` duplicate MIME warning**: Setting `sub_filter_types text/html;` triggers a `duplicate MIME type "text/html"` warning because `text/html` is already the default. **Fix**: omit the line entirely — `sub_filter_types` defaults to `text/html`.
- **`/favicon.ico` returning 404**: Browsers auto-request `/favicon.ico`. If no favicon file exists in the docroot, nginx logs a 404 on every page load. **Fix**: use `empty_gif` to return a 1x1 transparent GIF silently:
  ```nginx
  location = /favicon.ico {
      log_not_found off;
      access_log off;
      empty_gif;
  }
  ```
  Place this **before** the catch-all `location /` block. Returns HTTP 200 with `Content-Type: image/gif`.
- **Cloudflare caching stale 404/200 responses**: Through Cloudflare proxy (orange-cloud DNS), cached responses can persist long after origin content changes. `cf-cache-status: DYNAMIC` does NOT guarantee fresh content — Cloudflare edge nodes can serve stale cached pages for extended periods, especially when the same URL previously served content from a different backend.

  **Diagnostic flow**:
  1. Test local origin first: `curl -H 'Host: domain.com' http://127.0.0.1/path | head -3`
  2. If local is correct but Cloudflare shows stale content, add `Cache-Control: no-store, no-cache, must-revalidate` via nginx
  3. Even with correct headers, Cloudflare may still serve cached edge content — verify via `curl -sI https://domain.com/path | grep cf-cache-status`

  **Fix when cache is poisoned beyond header repair**:
  - **Short-term**: Use a cloudflared quick tunnel to bypass Cloudflare DNS proxy entirely:
    ```bash
    cd /path/to/static/files && python3 -m http.server 8081 &
    cloudflared tunnel --url http://localhost:8081
    # Use the generated *.trycloudflare.com URL
    ```
  - **Long-term**: Purge Cloudflare cache via API (requires `CLOUDFLARE_API_TOKEN`):
    ```bash
    curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"purge_everything":true}'
    ```
  - **Prevention**: Before deploying to a URL that previously served different backend content, use a unique new path first to verify Cloudflare returns fresh content, then restore the original path after cache expires.

## React SPA + API Backend Proxy Deployment

For Vite-built React SPAs that need an API backend (e.g., Telegram Mini Apps, dashboards), use this pattern:

### Architecture
```
nginx (443 SSL)
 ├── /m/index.html       ← Vite React SPA (auth_basic protected)
 ├── /assets/*           ← JS/CSS bundles (auth_basic protected, ^~ priority)
 └── /api/*              ← Proxied to backend server (NO auth, or separate)
       ↑
  Python backend (port 8081)
```

### Nginx Config (full minimal snippet)

```nginx
# ── HTTP → HTTPS redirect ──
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    root /var/www/brand-site;

    # ── Auth-protected SPA ──
    location /m/ {
        auth_basic "Restricted Area";
        auth_basic_user_file /etc/nginx/.htpasswd-miniapp;
        alias /var/www/brand-site/m/;
        try_files $uri $uri/ /m/index.html;
    }

    # ── Auth-protected assets (^~ stops regex from stealing the match) ──
    location ^~ /assets/ {
        auth_basic "Restricted Area";
        auth_basic_user_file /etc/nginx/.htpasswd-miniapp;
        alias /var/www/brand-site/m/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ── API backend proxy (no auth — backend is localhost only) ──
    location /api/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }
}
```

### Key Design Decisions

| Decision | Why |
|:---------|:----|
| auth_basic on `/m/` + `/assets/` | The SPA HTML loads assets by absolute path (`/assets/xyz.js`). If assets aren't also protected, the browser sends public asset requests that bypass auth, creating a confusing UX. Same realm → same cached credentials. |
| `^~ /assets/` not `/assets/` | Nginx processes **regex** locations (`~* \.(js|css|…)$`) before **prefix** locations. A regex like `try_files $uri =404` from root docroot will eat `/assets/index.js` before the `/assets/` alias gets a chance. `^~` tells nginx: "skip regex, this prefix wins." |
| `/api/` without auth | The API backend is localhost-only; it's not exposed externally except through nginx. Adding auth here would require the SPA (browser) to handle 401/Authorization headers — which the generic `fetch()` calls don't. |
| `alias` not `root` with `/m/` | `alias` replaces the full prefix path, while `root` appends. With `root`, `/m/index.html` would look for `/var/www/brand-site/m/m/index.html` (double `/m/`). Use `alias` for subdirectory SPAs. |

### Vite Build Config

The SPA HTML references assets with **absolute paths** (`/assets/index-xyz.js`), not relative. To change this, set `base` in `vite.config.ts`:

```ts
// vite.config.ts
export default defineConfig({
  base: '/m/',  // ← all asset paths become /m/assets/...
  build: { outDir: 'dist' },
})
```

If `base` is `/` (default), the SPA must be served at the domain root, not a subdirectory. Workaround when serving from a subdirectory: nginx `^~ /assets/` alias (shown above).

### Enabling SSL with Let's Encrypt

```bash
# Obtain certificate (port 80 must be free for standalone mode)
sudo nginx -s stop
sudo certbot certonly --standalone -d example.com -d www.example.com \
  --non-interactive --agree-tos --email your@email.com

# Restart nginx
sudo nginx
```

Add auto-renewal (certbot sets it up automatically, verify with):
```bash
sudo certbot renew --dry-run
```

### Mobile SPA: Swipe-Back Gesture

For mobile apps (Telegram Mini Apps, PWA), add touch swipe detection so users can swipe right to go back:

```tsx
// In the root router component:
const touchStartX = useRef(0);
const touchStartY = useRef(0);
const onTouchStart = (e: React.TouchEvent) => {
  touchStartX.current = e.touches[0].clientX;
  touchStartY.current = e.touches[0].clientY;
};
const onTouchEnd = (e: React.TouchEvent) => {
  if (isRoot) return; // don't swipe back from home
  const dx = e.changedTouches[0].clientX - touchStartX.current;
  const dy = e.changedTouches[0].clientY - touchStartY.current;
  // Left edge (<40px), swipe right (>80px), minimal vertical drift (<50px)
  if (touchStartX.current < 40 && dx > 80 && Math.abs(dy) < 50) {
    navigate(ROUTES.HOME);
  }
};

// Wrap content and set touchAction to allow vertical scroll
<div style={{ touchAction: 'pan-y' }}
     onTouchStart={onTouchStart}
     onTouchEnd={onTouchEnd}>
  {children}
</div>
```

**Touch-action `pan-y`** is critical: without it, the swipe handler blocks vertical scrolling on mobile.

### SPA Pitfall: Mock Data on Default Route

If the SPA contains a "mockup" or "dream" dashboard page that uses hardcoded data (no API calls), **do not set it as the default route**. The user opens the app and sees static fake data, thinking it's broken.

```tsx
// ❌ Bad: default route = mock data page
const [route, setRoute] = useState(ROUTES.DREAM);

// ✅ Good: default route = real API data page
const [route, setRoute] = useState(ROUTES.API_STATUS);
```

The mock page can remain accessible via navigation, but the entry point must always be real data.

### Telegram BotFather Registration

```text
① @BotFather → /setmenubutton
② Select the bot
③ Paste URL (e.g. https://example.com/m/)
④ Set button title (e.g. "📊 儀表板")
```
The button appears in the chat input area. The URL must be HTTPS and accessible.

## Removing the Configuration

To disable the protected admin interface:

1. Delete or comment out the `location /admin/` and `location /assets/` blocks.
2. Run `sudo nginx -t && sudo systemctl reload nginx`.
3. Optionally remove the password file: `sudo rm /etc/nginx/.htpasswd`.

## Replacing auth_basic with JWT Token Auth

When you want to replace nginx `auth_basic` popups with a branded login page + JWT tokens, follow this migration:

### Migration Steps

1. **Remove `auth_basic` from nginx** — delete all `auth_basic` and `auth_basic_user_file` lines, then reload:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

2. **Add JWT auth to the backend** — in each `do_GET`/`do_POST` handler, check `Authorization: Bearer <token>`, skip only `/api/auth/login`. Use HMAC-SHA256 tokens. Store files under `~/.hermes/env/.auth_secret` (auto-generated) and `~/.hermes/env/.auth_password` (bcrypt hash).

3. **Create a branded login page** (`/m/login.html`) — dark card, password input, POSTs to `/api/auth/login`, stores token in `localStorage('token')`, redirects to `/m/`.

4. **Update the SPA frontend** — create `src/hooks/useApi.ts` with `apiFetch()` that auto-attaches Bearer token + redirects on 401. In `AppRouter.tsx`, add `useEffect(() => requireAuth(), [])`. Replace all `fetch(...)` with `apiFetch(...)`.

5. **Deploy** — `npm run build`, copy to web root, restart backend.

### After-Migration Architecture

```
nginx (443, NO auth_basic)
 ├── /m/login.html     ← branded login page
 ├── /m/index.html     ← SPA (requires token)
 ├── /assets/*         ← public
 └── /api/*            ← Python backend
       ├── /api/auth/login    (public)
       └── ALL OTHER /api/*   (token required)
```

### Pitfall: Root User ~ Expansion

When the Python server runs via `sudo`, `os.path.expanduser("~")` resolves to `/root/`. Copy auth files:
```bash
sudo mkdir -p /root/.hermes/env
sudo cp ~/.hermes/env/.auth_* /root/.hermes/env/
sudo chmod 600 /root/.hermes/env/.auth_*
```

## References

- NGINX Basic Auth: https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html
- Proxy Pass Guide: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- SPA Routing Note: For SPA frameworks using HTML5 history mode, you may need a fallback `location / { try_files $uri $uri/ /index.html; }` – not required here as the backend serves the index.