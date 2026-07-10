# Cross-VM Domain-Down Diagnostics

## Session: 2026-07-10 — lucien126.com down, cron auth failure

### Scenario
- lucien126.com unresolvable from outside (ERR_CONNECTION_REFUSED)
- Local services on zhiyan-prod VM were all healthy
- DNS pointed to 136.117.107.221 (NOT this VM's IP 34.187.227.118)

### Diagnostic flow
1. `dig +short lucien126.com A` → 136.117.107.221
2. `curl -s ifconfig.me` → 34.187.227.118 (mismatch detected)
3. `gcloud compute instances list` → found `router-mvp` (e2-micro, us-west1-b) at 136.117.107.221
4. `gcloud compute ssh router-mvp --zone=us-west1-b` → discovered:
   - Node.js `/opt/free-api-router/server.js` running on port 8000
   - No nginx, no caddy, no web server on port 80/443
   - GCP firewall had `http-server` tag (OK)

### Fix applied
- Installed nginx + certbot via apt
- Created reverse proxy server block for lucien126.com → localhost:8000
- SSL via Let's Encrypt (lucien@lucien126.com)
- Fixed HTTP→HTTPS redirect (certbot defaults to `return 404`)
- Verified: HTTP 301 → HTTPS, /health returns 200

### Key lesson
Don't assume domain ownership — ask first. zhiyan.dev is NOT the user's domain.
