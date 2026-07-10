---
name: selfhost-hermes-web-tool
description: "Clone, build, and self-host a Hermes web dashboard from GitHub."
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [Hermes, Dashboard, Self-Host, GitHub, Deployment]
---

# Self-Host a Hermes Web Tool from GitHub

> ⚠️ **Important distinction**: This skill covers **third-party** web tools hosted on GitHub (e.g. `hermes-studio`, `hermes-proxy-console`).
> Hermes Agent also ships a **built-in** official web dashboard launched via `hermes dashboard`
> (FastAPI/Uvicorn, port 9119, 15 admin pages, OAuth/basic-auth). These are different things.
> See `references/official-web-dashboard.md` for the built-in dashboard's features and install guide.
> If the user can just run `hermes dashboard`, use that — it's the official, supported path.

Clone a Hermes-related web dashboard or admin tool from GitHub, install dependencies, configure it, and deploy it as a systemd-managed service behind nginx with cloudflared tunnel access.

Covers the full pipeline: GitHub search → requirements check → nvm → build → .env → systemd → nginx proxy → tunnel.

Does NOT cover: Docker-based deployments, Kubernetes, or non-Hermes tools.

## When to Use

- User says "裝起來" (install it) about a GitHub Hermes dashboard repo
- Need to evaluate and deploy a third-party Hermes admin/monitoring tool
- Need to expose a Hermes web UI behind nginx with auth
- Setting up a web-accessible dashboard with automatic restart

## Prerequisites

- nvm installed (`curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash`)
- Node.js 20+ (installed via nvm if not available)
- nginx with sudo access
- cloudflared installed (for temporary tunnel)
- Git

## Procedure

### 1. Evaluate the repository

```bash
# Search GitHub for Hermes dashboards
curl -s "https://api.github.com/search/repositories?q=hermes+agent+dashboard&sort=stars&order=desc&per_page=10" | python3 -c "
import json,sys; d=json.load(sys.stdin)
for r in d['items']:
    print(f\"{r['full_name']} ({r['stargazers_count']}★) - {r['description'] or 'no desc'}\")
    print(f\"  {r['html_url']}\")
"

# Check details of a specific repo
curl -s "https://api.github.com/repos/{owner}/{repo}" | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f\"Stars: {d['stargazers_count']}\")
print(f\"Language: {d['language']}\")
print(f\"License: {d.get('license',{}).get('spdx_id','N/A')}\")
print(f\"Topics: {d.get('topics',[])}\")
print(f\"Updated: {d['updated_at']}\")
"

# Check requirements
curl -sL "https://raw.githubusercontent.com/{owner}/{repo}/main/package.json" | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f\"Engines: {d.get('engines',{})}\")
print(f\"Deps: {list(d.get('dependencies',{}).keys())}\")
"
```

### 2. Install required Node version via nvm

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 20
nvm use 20
```

### 3. Clone and install

```bash
cd /home/ysga1
git clone --depth=1 https://github.com/{owner}/{repo}.git
cd {repo}
npm install
```

### 4. Configure

```bash
cp .env.example .env
# Edit .env: set PASSWORD, SECRET, PORT, HERMES_HOME
```

Use Python for safe sed (avoids password characters breaking sed):

```python
import re
with open('.env', 'r') as f: content = f.read()
content = re.sub(r'ENV_VAR=.*', 'ENV_VAR=VALUE', content)
with open('.env', 'w') as f: f.write(content)
```

### 5. Build the frontend

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20
npm run build
```

### 6. Create systemd service

```ini
[Unit]
Description=Tool Name
After=network.target

[Service]
Type=simple
User=ysga1
WorkingDirectory=/home/ysga1/{repo}
Environment=HOME=/home/ysga1
Environment=NVM_DIR=/home/ysga1/.nvm
Environment=PORT=10274
Environment=HOST=0.0.0.0
# Add all env vars from .env here
ExecStart=/bin/bash -c 'source $NVM_DIR/nvm.sh && nvm use 20 && node server.js'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable {service-name}
sudo systemctl start {service-name}
```

### 7. Verify the service

```bash
sudo systemctl status {service-name} --no-pager -l
ss -tlnp | grep {PORT}
curl -s -o /dev/null -w "%{http_code}" http://localhost:{PORT}/
```

### 8. Configure nginx proxy

Add a location block to the existing site:

```nginx
location /{path}/ {
    proxy_pass http://127.0.0.1:{PORT}/;
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

Add via Python (insert before the last `}` of the server block):

```python
with open('/etc/nginx/sites-available/{site}', 'r') as f:
    content = f.read()
lines = content.split('\n')
for i in range(len(lines)-1, -1, -1):
    if lines[i].strip() == '}':
        lines.insert(i, '{nginx_block}')
        break
with open('/etc/nginx/sites-available/{site}', 'w') as f:
    f.write('\n'.join(lines))
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 9. Open cloudflared tunnel for immediate access

```bash
terminal(background=true, watch_patterns=["https://","trycloudflare.com"]):
    cloudflared tunnel --url http://localhost:{PORT}
```

Check the process log for the tunnel URL, then tell the user.

### 10. Clean up old background processes

Old processes started via `terminal(background=true)` should be killed once systemd takes over. Use `process(action="kill", session_id="...")` or `kill {PID}` for each.

## Pitfalls

- **Node version mismatch**: Most Hermes dashboards require Node 20+. Use nvm to install and manage multiple versions. System Node (18) is too old for hermes-studio (needs 23+).
- **.env contains regex-special chars**: Passwords with `/`, `$`, or `\` break sed. Use Python or a proper env editor.
- **nginx config corruption**: Multiple sed/patch attempts can create nested location blocks or duplicate entries. Always run `sudo nginx -t` before reload. If corrupted, restore from backup (`sudo cp /etc/nginx/sites-available/{site}.backup /etc/nginx/sites-available/{site}`).
- **cloudflared URLs change on restart**: trycloudflare tunnels get a new random URL every time they restart. For permanent URLs, use a named tunnel with a Cloudflare account.
- **Port conflicts**: The default port of the dashboard tool (10272/10274) may conflict. Always check `ss -tlnp | grep {PORT}` before starting.
- **Build fails due to npm engine warnings**: `npm WARN EBADENGINE` is a warning, not an error. The build often works despite the warning. Check exit code, not stderr.
- **Killing old background processes**: Use `process(action="kill")` or `kill {PID}`. Old processes started earlier in the session may terminate silently when replaced.

## Verification

1. `sudo systemctl is-active {service-name}` → `active`
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:{PORT}/` → `200`
3. `curl -s -o /dev/null -w "%{http_code}" http://localhost/{nginx-path}/` → `200`
4. Open the cloudflared tunnel URL in browser → login page loads
