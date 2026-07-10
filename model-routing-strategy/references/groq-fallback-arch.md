# Groq 錯誤回退路由架構

## 路由策略
FreeLLM API 支援多種 `routing_strategy`：
- `smartest`：挑最高 intelligence_rank 的模型（預設，但錯誤時不回退）
- `auto`：按 profile priority 順序嘗試，錯誤時自動跳到下一個
- `priority`：依 profile 順序（不回退）
- `fastest`：挑最快的
- `balanced`：速度/品質/成本平衡

## 目前設定
- 策略：`auto`（2026-07-07 從 smartest 改為 auto）
- Profile 前 7 名：Groq 模型（gpt-oss-120b → llama-3.1-8b-instant → llama-3.3-70b-versatile → groq/compound → groq/compound-mini → gpt-oss-20b → safeguard-20b）
- 之後：qwen3-coder:free (openrouter) → gemini → mistral → nvidia（漸進）

## Groq Key Rotation
- Groq 允許最多 50 把獨立 API key，每把各自有 FREE tier 配額
- 當一把 key 被限速時，自動換下一把
- Key 管理腳本：`/usr/local/bin/groq-rotate.py`
- Key 儲存：`~/.hermes/env/groq-{label}.env`

## 健康監控
- Mini App Dashboard：每 5 分鐘 cron 更新 `/m/api/status.json`
- 監控走 API 不走 SSH：用 FreeLLM `/v1/models` + OpenRouter `/api/v1/credits`

## Mini App Backend
- 單一 Python server (`/usr/local/bin/miniapp-server.py`) 同時 serve：
  - 靜態檔（品牌頁）
  - API 端點（`/api/status`、`/api/models`、`/api/keys`、`/api/keys/add`）
- Tunnel URL 變動時需要重新綁定 BotFather
