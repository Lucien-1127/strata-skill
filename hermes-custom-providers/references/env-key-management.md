# 環境變數金鑰實務 — 2026-07-09 實戰

## 全系統金鑰位置盤點

### 主要存放區 `~/.hermes/env/`（每平台每標籤一個 .env）

| 檔案 | 金鑰 | 用途 |
|------|------|------|
| `agnes-主帳號-Token-Plan-Starter.env` | `AGNES_API_KEY` | Token Plan 月費（圖片/影片） |
| `deepseek-主帳號.env` | `DEEPSEEK_API_KEY` | DeepSeek 主 key（現役） |
| `freellm-本機.env` | `FREELMAPI_KEY` | FreeLLM 本機 router |
| `groq-測試.env` | `GROQ_API_KEY` | Groq 測試 key |
| `openrouter-主帳號.env` | `OPENROUTER_API_KEY` | OpenRouter 主 key |
| `telegram-bot-太陽.env` | `TELEGRAM_BOT_TOKEN` | TG Bot |

### Hermes 全域 `~/.hermes/.env`（gateway 自動載入）

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_API_URL=https://api.telegram.org
GATEWAY_ALLOW_ALL_USERS=true
DEEPSEEK_API_KEY=sk-...     ← 與 env/ 重複但 gateway 需要
OPENAI_API_KEY=sk-...       ← 供 mem0 OpenAI client 檢查用
```

### systemd 層級 `env.conf`（gateway 專用）

```
OPENROUTER_API_KEY=sk-or-...  ← 供 Hermes fallback 路由使用
```

## 已從 config 移除 inline key 的檔案

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `~/.hermes/config.yaml` | ✅ 無 inline key | custom_providers 已移除 api_key 欄位 |
| `~/.hermes/mem0.json` | ✅ `_FROM_ENV_` 佔位符 | 由 save_summary_to_mem0.py 注入 |
| `~/.hermes/auth.json` | ✅ Hermes 防讀保護 | 金鑰存在但 read_file 拒絕存取 |
