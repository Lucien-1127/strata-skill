# FastAPI 後端架構筆記 (v2)

## 架構總覽

單檔案 FastAPI（`main.py`），整合 auth + model CRUD + api_entry CRUD + dashboard + health probe。

```
/m/api/*  → nginx proxy → localhost:8082 → uvicorn main:app
```

## 核心元件

| 元件 | 實作 |
|------|------|
| 資料庫 | SQLite（透過 `sqlite3` stdlib，無需 ORM） |
| 認證 | HMAC-SHA256 JWT（`python-jose` + `bcrypt`），僅密碼無用戶名 |
| 密碼 | bcrypt hash 存於 `~/.hermes/env/.auth_password` |
| 運行 | systemd service `hermes-miniapp`，監聽 port 8082 |

## JWT 簽署機制

雙重密鑰：一半來自 HMAC keyfile（`~/.hermes/env/.jwt_hmac`），一半來自 `JWT_SECRET` 環境變數。

```python
def get_jwt_key() -> str:
    """合併 HMAC file + env var 成 JWT 簽署密鑰"""
    hmac_key = os.environ.get("JWT_HMAC_KEY", "")
    if not hmac_key:
        try:
            with open(os.path.expanduser("~/.hermes/env/.jwt_hmac")) as f:
                hmac_key = f.read().strip()
        except FileNotFoundError:
            hmac_key = secrets.token_hex(32)
    env_key = os.environ.get("JWT_SECRET", "hermes-miniapp-prod-secret")
    return hmac.SHA256((hmac_key + env_key).encode()).hexdigest()
```

## Token 結構

```python
def create_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "admin",
        "iat": int(now.timestamp()),  # numeric, not ISO string!
        "exp": int(now.timestamp() + JWT_TTL),
    }
    return jwt.encode(payload, get_jwt_key(), algorithm="HS256")
```

> ⚠️ `iat` 必須是 numeric timestamp，若放 ISO string 會導致 `jwt.decode()` 驗證失敗。

## 驗證 middleware

```python
def verify_token(request: Request) -> None:
    """在每個需要 auth 的端點開頭呼叫"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, ...)
    token = auth[7:]
    try:
        jwt.decode(token, get_jwt_key(), algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, ...)
```

## 回應格式

所有 API 回應統一格式：

```json
{
  "ok": true,
  "data": <payload>,
  "meta": {"timestamp": "ISO8601", "cache": false}
}
```

錯誤：
```json
{
  "detail": {"error": {"code": "UNAUTHORIZED", "message": "請先登入"}}
}
```

## 資料表結構

```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT DEFAULT '',
    description TEXT DEFAULT '',
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES models(id),
    endpoint TEXT NOT NULL,
    key_alias TEXT DEFAULT '',
    quota_limit INTEGER DEFAULT 0,
    usage INTEGER DEFAULT 0,
    quota_remaining INTEGER DEFAULT 0,
    rate_limited INTEGER DEFAULT 0,
    rate_reset_at TEXT,
    last_seen TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 啟動

```bash
cd /home/ysga1/hermes-miniapp/backend
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8082
```

### systemd unit

```ini
[Service]
User=ysga1
WorkingDirectory=/home/ysga1/hermes-miniapp/backend
ExecStart=/home/ysga1/hermes-miniapp/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8082
Environment=HERMES_DATA_DIR=/home/ysga1/hermes-miniapp/data
Environment=JWT_SECRET=hermes-miniapp-prod-secret-k8x9m2
Restart=always
RestartSec=3
```

## 依賴

```
fastapi
uvicorn
python-jose[cryptography]
bcrypt
```

安裝：`pip install fastapi uvicorn sqlalchemy python-jose bcrypt httpx`
（`sqlalchemy` 和 `httpx` 可選，當前未使用但已裝以備將來擴充）
