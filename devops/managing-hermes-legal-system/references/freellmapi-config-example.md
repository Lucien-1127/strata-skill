# FreeLLM API Configuration Example

## File Location
`/opt/zhiyan/freellmapi.config.json`

## Current Configuration
```json
{
  "keys": [],
  "customProviders": [
    {
      "baseUrl": "https://apihub.agnes-ai.com/v1",
      "apiKey": "cpk-...",
      "label": "Agnes AI",
      "models": [
        {
          "model": "agnes-2.0-flash",
          "displayName": "Agnes Flash 2.0",
          "supportsTools": true
        },
        {
          "model": "agnes-2.0-pro",
          "displayName": "Agnes Pro 2.0",
          "supportsTools": true
        }
      ]
    }
  ],
  "fallback": [
    { "platform": "custom", "modelId": "agnes-2.0-flash", "priority": 1 },
    { "platform": "custom", "modelId": "agnes-2.0-pro", "priority": 2 },
    { "platform": "google", "modelId": "gemini-2.5-flash", "priority": 3 },
    { "platform": "nvidia", "modelId": "moonshotai/kimi-k2.6", "priority": 4 }
  ],
  "routing": {
    "strategy": "priority"
  }
}
```

## Docker Container Info
- Container name: `zhiyan-freellmapi-1`
- Image: `ghcr.io/tashfeenahmed/freellmapi:latest`
- Port: `127.0.0.1:3001`
- Config is loaded via: `FREEAPI_CONFIG_PATH=/app/server/data/freellmapi.config.json`
- Database: `/app/server/data/freeapi.db` (SQLite)

## Key Fields
| Field | Description |
|-------|-------------|
| `keys` | API keys for various LLM providers |
| `customProviders` | Custom provider configurations |
| `fallback` | Fallback models in priority order |
| `routing.strategy` | Routing strategy (e.g., "priority") |

## After Editing
1. Copy updated config to container: `docker cp /opt/zhiyan/freellmapi.config.json zhiyan-freellmapi-1:/app/server/data/freellmapi.config.json`
2. Restart container: `sudo docker restart zhiyan-freellmapi-1`

## Database Access (for password reset, etc.)
- Database file: `/opt/zhiyan/freellmapi.config.json` (host)
- Container path: `/app/server/data/freeapi.db`
- Copy out: `docker cp zhiyan-freellmapi-1:/app/server/data/freeapi.db /tmp/freeapi.db`
- Users table: `SELECT * FROM users LIMIT 5;`
- Settings table: `SELECT * FROM settings LIMIT 5;`