# JWT Auth System — Hermes Proxy Console

This reference documents the JWT authentication system implemented in v4 of the Hermes Proxy Console, replacing nginx `auth_basic` with a branded login page + token-based API auth.

## Architecture

```
Browser                          Backend (port 8081)
  │                                  │
  ├── GET /m/login.html ──────────→  │  (static HTML, no auth needed)
  ├── POST /api/auth/login ───────→  │  verify bcrypt → return token
  ├── localStorage.setItem('token') │
  ├── apiFetch('/api/status') ────→  │  Authorization: Bearer <token> → 200
  ├── apiFetch('/api/keys') ──────→  │  Authorization: Bearer <token> → 200
  │                                  │
  └── (token expired) ───────────→  │  401 → auto-redirect to /m/login.html
```

## Backend Implementation

### Auth Files (`~/.hermes/env/`)

| File | Content | Security |
|---|---|---|
| `.auth_secret` | 64-char hex HMAC key | `chmod 600`, auto-generated |
| `.auth_password` | bcrypt hash of password | `chmod 600`, manually created |

### Token Format (HMAC-SHA256)

```
payload = "admin:{unix_expiry}"
signature = HMAC-SHA256(secret, payload) → hex
token = base64url(payload + ":" + signature)
```

Expiry is **embedded in the payload** — encoded in the token itself, no server-side session store needed.

### Key Functions

```python
import hmac, hashlib, base64, time, bcrypt

SECRET_FILE = os.path.expanduser("~/.hermes/env/.auth_secret")
PASSWORD_FILE = os.path.expanduser("~/.hermes/env/.auth_password")
TOKEN_TTL = 86400  # 24h

def _load_secret():
    # Auto-generates if missing (secrets.token_hex(32))
    ...

def _generate_token(user_id="admin"):
    secret = _load_secret()
    expiry = int(time.time()) + TOKEN_TTL
    payload = f"{user_id}:{expiry}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode().rstrip("=")

def _verify_token(token):
    # Decode, split payload:sig, recompute HMAC, compare, check expiry
    ...

def _verify_password(password):
    # bcrypt.checkpw(password, stored_hash)
    ...
```

### Endpoint Protection

All API endpoints call `_require_auth()` before processing, except `/api/auth/login`:

```python
def _require_auth(self):
    token = _get_token_from_headers(self.headers)  # "Bearer xyz" → "xyz"
    if not token or not _verify_token(token):
        self._json({"error":"未授權，請重新登入","code":"UNAUTHORIZED"}, 401)
        return True
    return False

def do_GET(self):
    path = urlparse(self.path).path
    if path == "/api/auth/login":
        # skip auth
    else:
        if self._require_auth(): return
    # ... handle endpoint ...
```

## Frontend Implementation

### `src/hooks/useApi.ts`

```typescript
const TOKEN_KEY = 'token';
const LOGIN_URL = '/m/login.html';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function redirectToLogin(): void {
  window.location.href = LOGIN_URL;
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = { ...(init?.headers as Record<string, string>) };

  // Don't add auth header for login itself
  const url = typeof input === 'string' ? input : input.url;
  if (!url.includes('/api/auth/login') && token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(input, { ...init, headers });

  if (res.status === 401 && !url.includes('/api/auth/login')) {
    clearToken();
    redirectToLogin();
    throw new Error('未授權，請重新登入');
  }

  return res;
}

export function requireAuth(): boolean {
  if (!getToken()) {
    redirectToLogin();
    return false;
  }
  return true;
}
```

### AppRouter Token Check

```typescript
import { requireAuth } from '../../hooks/useApi';

export const AppRouter: FC = () => {
  useEffect(() => { requireAuth(); }, []);
  // ...
};
```

Per-page replacement: change `fetch(...)` → `apiFetch(...)` and add `import { apiFetch } from '../../hooks/useApi';`.

## Login Page (`/m/login.html`)

Dark theme card layout (`background: #1e293b` in `#0f172a` container):
- Password input with `autocomplete="current-password"`
- Green submit button (`#22c55e`)
- Error message div (hidden by default, `#ef4444`)
- Enter key submits via `keydown` listener
- On success: `localStorage.setItem('token', data.token)` → `window.location.href = '/m/'`

Full source is at `/var/www/brand-site/m/login.html`.

## Nginx Changes

Before (with auth_basic):
```nginx
location /m/ { auth_basic ...; alias /var/www/brand-site/m/; }
location ^~ /assets/ { auth_basic ...; alias ...; }
```

After (no auth_basic):
```nginx
location /m/ { alias /var/www/brand-site/m/; }
location ^~ /assets/ { alias ...; }
```

Auth is now handled entirely by the backend's `_require_auth()`. Static HTML/JS/CSS are publicly served — the app protects itself at the API layer.

## Pitfalls

### Root User ~ Expansion

When the server runs via `sudo python3 /usr/local/bin/miniapp-server.py`, `os.path.expanduser("~/.hermes/env/.auth_secret")` resolves to `/root/.hermes/env/` — **not** `/home/ysga1/.hermes/env/`.

**Symptom**: Login returns `401 密碼錯誤` even with correct password, because the server is reading a non-existent password file in `/root/`.

**Fix**:
```bash
sudo mkdir -p /root/.hermes/env
sudo cp ~/.hermes/env/.auth_* /root/.hermes/env/
sudo chmod 600 /root/.hermes/env/.auth_*
```
