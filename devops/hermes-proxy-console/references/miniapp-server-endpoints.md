# Mini App Server — API Endpoints Reference

## Server Overview

Python stdlib HTTP server at `/usr/local/bin/miniapp-server.py`, serves both the SPA static files and JSON API on a single port (default 8081). No framework — `SimpleHTTPRequestHandler` with manual routing.

## Database

SQLite DB at `/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db`

### `requests` Table Schema

```sql
CREATE TABLE requests (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  platform      TEXT NOT NULL,
  model_id      TEXT NOT NULL,
  key_id        INTEGER,
  status        TEXT NOT NULL,
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  latency_ms    INTEGER NOT NULL DEFAULT 0,
  error         TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  ttfb_ms       INTEGER,
  requested_model TEXT,
  request_type  TEXT NOT NULL DEFAULT 'chat'
);
CREATE INDEX idx_requests_created_at ON requests(created_at);
CREATE INDEX idx_requests_platform ON requests(platform);
CREATE INDEX idx_requests_key_id ON requests(key_id);
```

### `models` Table (from `_get_model_status`)

```sql
-- Referenced columns: platform, COUNT(*), SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END)
```

### `provider_quota_state` Table (from `_get_dash_status`)

```sql
-- Referenced columns: key_id, limit_value, remaining_value, limit_type
-- JOINs with api_keys ON provider_quota_state.key_id = api_keys.id
```

## Key Registry

JSON file at `~/.hermes/env/keys-registry.json`. Array of objects with fields:
`id` (md5 first 8), `platform`, `label`, `prefix`, `added_at`, `env_file`, `tested`, `valid`, `last_tested?`, `test_result?`

## All Endpoints

### Dashboard / Status

| Method | Endpoint | Returns | Source |
|---|---|---|---|
| GET | `/api/status` | Synthetic dashboard status | `_get_dash_status()` — docker, curl health checks, groq quota from DB, 7d daily token aggregation |
| GET | `/api/dashboard` | Complete dashboard payload (KPI cards + trends + alerts + events) | `_get_dashboard_payload()` — wraps `_get_dash_status()` with KPI structure |
| GET | `/api/models` | `{ platforms[], errors[], recent[] }` | DB queries on `requests` and `models` tables |
| GET | `/api/keys` | `{ keys: KeyItem[], platforms: string[] }` | Registry file + PLATFORM_CFG keys |

### New Endpoints (added in v3)

#### `GET /api/alerts`

Returns last 20 error requests (status ≠ 'success'):

```json
[
  {
    "id": 3120,
    "platform": "opencode",
    "model_id": "deepseek-v4-flash-free",
    "status": "error",
    "error": "The operation was aborted (opencode, chat, 15s)",
    "created_at": "2026-07-09 09:51:59"
  }
]
```

**Backend query:** `SELECT id, platform, model_id, status, error, created_at FROM requests WHERE status!='success' ORDER BY id DESC LIMIT 20`

#### `GET /api/proxy/status`

Returns service health + request stats:

```json
{
  "services": [
    { "name": "FreeLLM", "status": "ok", "detail": "Up 2 hours (healthy)" },
    { "name": "zhiyan-legal", "status": "ok", "detail": "HTTP 200" },
    { "name": "Qdrant", "status": "ok", "detail": "HTTP 200" }
  ],
  "stats": {
    "total_requests": 3121,
    "today_requests": 36,
    "total_errors": 1664,
    "error_rate": 53.32
  }
}
```

**Health checks:**
- FreeLLM: `docker ps --filter name=freellm --format "{{.Status}}"`
- zhiyan-legal: `curl http://127.0.0.1:8001/` (expect 200/000/302/307)
- Qdrant: `curl http://127.0.0.1:6333/` (expect 200/000/302/307)

**Stats queries:**
- total: `SELECT COUNT(*) FROM requests`
- today: `SELECT COUNT(*) FROM requests WHERE DATE(created_at)=DATE('now')`
- errors: `SELECT COUNT(*) FROM requests WHERE status!='success'`

#### `GET /api/settings/profile`

Returns system configuration summary:

```json
{
  "current_provider": "groq",
  "enabled_platforms": 6,
  "platform_list": ["agnes", "deepseek", "freellm", "groq", "openrouter", "telegram"],
  "api_keys_total": 8,
  "system_version": "v3.0.0"
}
```

**Source:** `load_registry()` → count platforms + keys. `current_provider` reads the most recent platform from `SELECT DISTINCT platform FROM requests ORDER BY id DESC LIMIT 1`.

### Key Management (CRUD)

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| POST | `/api/keys/add` | `{ platform, label, key }` | `{ success, id, label, platform, env_file, total }` |
| POST | `/api/keys/test` | `{ id }` | `{ success, id, platform, label, result }` |
| POST | `/api/keys/delete` | `{ id }` | `{ success, deleted, total }` |
| POST | `/api/keys/replace` | `{ id, key, label? }` | `{ success, id, old_label, new_label, platform }` |

Key validation: each platform has a `prefix` rule and a `test_url` with header template in `PLATFORM_CFG`.

### Proxy Action

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| POST | `/api/proxy/action` | `{ action: "restart" }` | `{ success, message }` or `{ success, error }` |

Currently only supports `action: "restart"` (runs `sudo systemctl restart hermes-proxy`).

### Auth Endpoints (added in v4)

#### `POST /api/auth/login`

Authenticates with password, returns JWT token. The only endpoint accessible without a token.

**Request:**
```json
{ "password": "Ting7809" }
```

**Response (200):**
```json
{
  "success": true,
  "token": "YWRtaW46MTc0MTU...",
  "expires_in": 86400
}
```

**Response (401):** `{ "error": "密碼錯誤" }`

**Auth mechanics:**
- Password verified via bcrypt against `~/.hermes/env/.auth_password`
- Token is HMAC-SHA256: `base64(user_id:expiry:hmac_hex)` with key from `~/.hermes/env/.auth_secret`
- TTL: 86400s (24h)

### Auth Enforcement (v4)

- All GET/POST endpoints (except `/api/auth/login`) require `Authorization: Bearer <token>`
- 401 response: `{"error":"未授權，請重新登入","code":"UNAUTHORIZED"}`
- Frontend `apiFetch()` helper in `src/hooks/useApi.ts` auto-attaches token + redirects on 401

### Auth Files in `~/.hermes/env/`

| File | Purpose | Generated |
|---|---|---|
| `.auth_secret` | 64-char hex HMAC key | Auto-generated on first boot |
| `.auth_password` | bcrypt hash of login password | Manual — `passlib.hash.bcrypt` |

**⚠️ Root user pitfall**: When the Python server runs via `sudo` (e.g. manual start), `os.path.expanduser("~")` resolves to `/root/.hermes/env/`, not the original user's home. Copy auth files:
```bash
sudo mkdir -p /root/.hermes/env
sudo cp ~/.hermes/env/.auth_* /root/.hermes/env/
sudo chmod 600 /root/.hermes/env/.auth_*
```

| Method | Endpoint | Returns |
|---|---|---|
| POST | `/api/alerts/:id/acknowledge` | `{ success, message: "告警已確認" }` |
| POST | `/api/alerts/:id/resolve` | `{ success, message: "告警已解決" }` |

## How to Add a New Endpoint

1. **In `do_GET`**: Add an `elif path == "/api/your-endpoint": self._json(self._your_method())`
2. **Write the helper method** on the `AppHandler` class. Use `self._q(sql)` for DB queries, `load_registry()` for key data, `subprocess.run()` for shell checks.
3. **`_q(sql, params)`** helper returns raw SQLite rows. Always handle empty results gracefully (empty list fallback).
4. **Frontend fetch**: use relative URLs (`/api/your-endpoint`) — never `localhost` (TG Mini App's WebView interprets `localhost` as the mobile device).

## Pitfalls

- **Server runs as a specific user** (not always root). When testing via `sudo`, `~` in `REGISTRY` path expands to `/root/.hermes/` instead of the actual user's home. The production systemd process runs as the correct user.
- **No systemd service defined** for miniapp-server currently. It's typically started manually via terminal or screen.
- **DB access** from the server uses the hardcoded path `/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db` — ensure this path is accessible to the running process.
- **`PLATFORM_CFG`** defines 11 platforms with per-platform test endpoint, prefix rule, and auth header template. Add new platforms here.
