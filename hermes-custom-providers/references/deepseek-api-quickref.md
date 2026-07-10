# DeepSeek API 配置速查表

## 快速配置命令

### 方式 1: custom_providers 列表（推薦，支援多 provider）

```bash
# 1. 編輯 ~/.hermes/config.yaml，添加 deepseek 條目
custom_providers:
  - name: deepseek
    api_key: sk-YOUR_KEY
    base_url: https://api.deepseek.com/v1
    api_mode: chat_completions
    model: deepseek-v4-pro
    models:
      deepseek-v4-pro:
        context_length: 128000

# 2. 設定預設模型
hermes config set model.provider custom:deepseek
hermes config set model.default deepseek-v4-pro

# 3. 驗證
hermes chat -q "Hello, respond in 3 words."
```

### 方式 2: providers 字典（簡單直接）

```bash
hermes config set providers.deepseek.base_url https://api.deepseek.com/v1
hermes config set providers.deepseek.api_key sk-YOUR_KEY
hermes config set providers.deepseek.api_mode chat_completions
hermes config set providers.deepseek.model deepseek-v4-pro
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-pro
```

## 模型切換

| 模型 | 特性 | 適合場景 |
|------|------|---------|
| `deepseek-v4-flash` | ⚡ 快速、低成本 | 日常對話、簡單任務 |
| `deepseek-v4-pro` | 🧠 高推理、最佳品質 | 複雜分析、架構設計 |

```bash
# 切換到 Flash
hermes config set model.default deepseek-v4-flash

# 切換到 Pro
hermes config set model.default deepseek-v4-pro
```

## 驗證與測試

### 直接 API 測試（curl）

```bash
curl -s -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' | python3 -m json.tool
```

### 模型列表查詢

```bash
curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer sk-YOUR_KEY" | python3 -c "import sys,json;print(json.dumps(json.load(sys.stdin)['data'], indent=2))"
```

## 常見錯誤排查

| 錯誤 | 原因 | 解決方式 |
|------|------|---------|
| `HTTP 401` | API key 無效 | 檢查金鑰是否正確，或重新產生 |
| `HTTP 400: invalid_request_error` | 模型名稱錯誤 | 不要在 `model.default` 加 `custom:deepseek/` 前綴 |
| `Provider resolver returned an empty API key` | 金鑰位置錯誤 | 確認金鑰在 `custom_providers` 或 `providers` 中 |

## 實測數據（2026-07-06）

| 模型 | 回應時間 | Context | 成本（相對） |
|------|---------|---------|-------------|
| V4 Pro | ~7-8s | 128K | 1x（基準） |
| V4 Flash | ~7-8s | 128K | ~0.3x |

## API 金鑰來源

1. 前往 [DeepSeek API Keys](https://platform.deepseek.com/api_keys)
2. 產生新的 API key
3. 複製金鑰並配置到 Hermes

## 相關文件

- `hermes-custom-providers/SKILL.md` — 完整配置指南
- `deepseek-agnes-routing/SKILL.md` — DeepSeek V4 路由策略