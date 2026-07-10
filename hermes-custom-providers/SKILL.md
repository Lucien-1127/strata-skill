---
name: hermes-custom-providers
description: "Configure custom/third-party API providers (OpenAI-compatible) in Hermes, set up credential pooling with multiple keys, "
---
# hermes-custom-providers

## 📖 Description

Configure custom/third-party API providers (OpenAI-compatible) in Hermes, set up credential pooling with multiple keys, and wire delegation sub-agents to separate keys.

---

# Hermes Custom Providers

Configuring a provider Hermes doesn't ship a built-in adapter for — any OpenAI-compatible API that needs `model.provider: custom` with a `base_url`, `api_key`, and `model.default`. Covers credential pooling for rate-limit circumvention and delegation sub-agent key separation.

**When to load**: user asks to switch to a new LLM provider, add sub-agent keys, pool multiple API keys, or debug credential issues.

## 核心鐵律：金鑰不得存在 config.yaml

**API keys 必須只存放在以下位置：**
- `~/.hermes/auth.json`（credential pool，Hermes 內部管理）
- `~/.hermes/.env`（環境變數檔案，`echo 'KEY=val' >> ~/.hermes/.env`）
- `~/.config/systemd/user/hermes-gateway.service.d/env.conf`（gateway 專用環境變數）

**禁止將 `api_key` 寫入 `~/.hermes/config.yaml` 的：**
- `custom_providers` 條目
- `providers.<name>` 區塊
- `model.api_key` 欄位

**為什麼：**
1. `read_file` / `terminal` 工具會顯示設定檔內容，config.yaml 是常用查閱對象
2. `hermes config set` 寫入的 key 也進 config.yaml，而非專用安全儲存
3. credential pool (`auth.json`) 有 Hermes 的防讀保護（`read_file` 會拒絕存取）
4. 環境變數 (`~/.hermes/.env`) 只有啟動時載入，不會被工具無意間讀取

**推薦做法：**

```bash
# ✅ 正確：key 只放 .env，config.yaml 不放 key
echo 'DEEPSEEK_API_KEY=sk-xxx...' >> ~/.hermes/.env
# config.yaml 中 custom_providers 條目不要有 api_key 欄位

# ✅ 正確：第三方設定檔（mem0.json 等）用佔位符 + 環境變數注入
# mem0.json:
#   "api_key": "_FROM_ENV_DEEPSEEK_"
# Python wrapper:
#   api_key = os.environ["DEEPSEEK_API_KEY"]
```

**有 inline api_key 的常見症狀（用戶會立刻發現並生氣）：**
- 用戶要求提供設定檔給查看 → 檔裡有明碼金鑰
- 用戶要求確認路由配置 → config.yaml 裡 key 直接曝光
- 用戶發現金鑰在 Git 版本控制中 → 已違反資安規範

---

## 1. Basic Custom Provider Setup

```bash
hermes config set model.provider custom
hermes config set model.base_url https://api.provider.com/v1
hermes config set model.api_key sk-xxx...
hermes config set model.default model-name
```

The base URL **must end with `/v1`**, not `/v1/chat/completions` (unless the provider explicitly requires the full path).

Verify:
```bash
hermes chat -q "Hello, respond in one word."
```

---

## 2. Credential Pooling (Multiple API Keys)

When a provider has rate limits (e.g. 20 RPM free tier), pool multiple keys to increase throughput. The pool auto-rotates keys in `round_robin`.

### 2.1 Add a named provider entry

```bash
hermes config set providers.<name>.base_url https://apihub.agnes-ai.com/v1
hermes config set providers.<name>.api_key sk-xxx...
```

This creates a credential pool entry under `custom:<name>` in `auth.json`.

### 2.2 Add more keys to the pool

Edit `~/.hermes/auth.json` — the credential pool section. Each entry needs:
```json
{
  "id": "unique-id",
  "label": "descriptive-name",
  "auth_type": "api_key",
  "priority": 0,
  "source": "manual",
  "api_key": "sk-full-key-here"
}
```

Or use environment references: a `providers.<name>.api_key` in `config.yaml` auto-registers as `source: "config:<name>"`.

### 2.3 Set rotation strategy

```bash
hermes config set credential_pool_strategies.<name> round_robin
```

Supported strategies: `round_robin`, `random`, `fill_first` (default).

### 2.4 Verify the pool

```bash
cat ~/.hermes/auth.json | python3 -c "import sys,json;d=json.load(sys.stdin);cp=d.get('credential_pool',{});[print(f'{k}: {len(v)} keys') for k,v in cp.items()]"
```

---

## 3. Delegation (Sub-Agent) Key Management

Delegation can use its own provider/key separate from the main model.

### 3.1 Direct key (single delegation key)

```bash
hermes config set delegation.provider custom
hermes config set delegation.base_url https://api.provider.com/v1
hermes config set delegation.api_key sk-xxx...
hermes config set delegation.model model-name
```

### 3.2 Provider-referenced key (uses credential pool)

```bash
hermes config set delegation.provider <name>
hermes config set delegation.base_url https://api.provider.com/v1
hermes config set delegation.model model-name
```

⚠️ **Critical: delegation.api_key 和 delegation.api_mode 必須明確設定**

即使 `delegation.provider` 指向一個已配置的 provider，子代理仍然可能因為 `delegation.api_key` 為空而失敗（HTTP 401）。

**必須同時執行：**
```bash
hermes config set delegation.api_key "您的API金鑰"
hermes config set delegation.api_mode chat_completions
```

`hermes config set` 會將金鑰寫入 AppData 的 config.yaml。僅設定 `providers.<name>.api_key` 是不夠的 — delegation 子代理有自己的 api_key 欄位需要填寫。

### 3.3 用戶金鑰偏好（Agnes AI 案例）

用戶明確指定：**所有 Agnes 相關 API 金鑰統一使用 `cpk-` 前綴的月費金鑰。**

| 金鑰類型 | 前綴 | 狀態 | 適用 |
|---------|------|------|------|
| Token Plan 月費 | `cpk-...` | ✅ 可正常工作 | 所有 Agnes 服務（chat/image/video） |
| Nous Portal | `sk-nous-...` | ❌ 401 無效 | 已廢棄，不可用 |

金鑰配置統一走：
```bash
# Provider 層
hermes config set providers.agnes.api_key "cpk-YOUR_KEY"
hermes config set providers.agnes.base_url https://apihub.agnes-ai.com/v1

# Delegation 層（子代理）
hermes config set delegation.api_key "cpk-YOUR_KEY"
hermes config set delegation.api_mode chat_completions
hermes config set delegation.provider agnes
hermes config set delegation.base_url https://apihub.agnes-ai.com/v1
hermes config set delegation.model agnes-2.0-flash
```

### 3.4 Pool strategies for delegation

Set `credential_pool_strategies.<name>` to control how pooled keys are selected for sub-agent calls. `round_robin` distributes load across all keys.

---

## 4. Pitfalls

### 4.0 DeepSeek API 配置（OpenAI-compatible）

**官方 API 端點：**\n- **Base URL**: `https://api.deepseek.com/v1`\n- **API Key**: 從 [DeepSeek API Keys](https://platform.deepseek.com/api_keys) 獲取\n- **模型列表**:\n  - `deepseek-v4-flash` (V4 Flash，預設推薦)\n  - `deepseek-v4-pro` (V4 Pro，高品質推理)\n  - `deepseek-v3` (V3，舊世代)\n  - `deepseek-coder` (程式碼專用)\n\n> **⚠️ 2026-07-09 重要公告：** DeepSeek 已宣布舊模型名 `deepseek-chat` 與 `deepseek-reasoner` 將於 **2026-07-24 停止使用**。目前這兩個名稱分別指向 `deepseek-v4-flash` 的非思考模式與思考模式。務必在此之前全面改用 `deepseek-v4-flash` / `deepseek-v4-pro`。\n> 任何專案中仍使用 `deepseek-chat` 的地方（如 zhiyan-legal `server.py` 的 fallback 值），即使目前沒在用，也建議一次改掉。舊名停用後，打 `deepseek-chat` 會直接 404。

**推薦配置方式（custom_providers 列表）：**
```bash
# 使用 custom:deepseek 提供者（推薦，支援多 provider 切換）
# 步驟 1: 在 custom_providers 列表添加 deepseek 條目
# 編輯 ~/.hermes/config.yaml:
custom_providers:
  - name: deepseek
    api_key: sk-YOUR_DEEPSEEK_KEY
    base_url: https://api.deepseek.com/v1
    api_mode: chat_completions
    model: deepseek-v4-pro
    models:
      deepseek-v4-pro:
        context_length: 128000
        name: DeepSeek V4 Pro

# 步驟 2: 設定預設模型
hermes config set model.provider custom:deepseek
hermes config set model.default deepseek-v4-pro

# 步驟 3: 切換到 Flash 模型（更快更便宜）
hermes config set providers.deepseek.model deepseek-v4-flash
hermes config set model.default deepseek-v4-flash
```

**替代方式（直接 provider 配置）：**
```bash
# 直接設定 provider（適用於單一場景）
hermes config set providers.deepseek.base_url https://api.deepseek.com/v1
hermes config set providers.deepseek.api_key sk-YOUR_DEEPSEEK_KEY
hermes config set providers.deepseek.api_mode chat_completions
hermes config set providers.deepseek.model deepseek-v4-pro
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-pro
```

**關鍵配置差異：**
| 配置方式 | model.provider | model.default | 優點 |
|---------|---------------|---------------|------|
| `custom_providers` 列表 | `custom:deepseek` | `deepseek-v4-pro` | ✅ 支援多 provider，易於切換 |
| `providers` 字典 | `deepseek` | `deepseek-v4-pro` | ✅ 簡單直接，單一場景 |

**注意事項：**
- Base URL **必須** 以 `/v1` 結尾，不要加 `/chat/completions`
- 使用 V4 模型時，建議優先選擇 `deepseek-v4-flash`（速度快、成本低）
- V4 Pro 適用於需要最高品質的複雜推理任務
- V4 模型支援 128K context window（實測驗證）

**實測數據（DeepSeek V4 Pro）：**
- 回應時間：~7-8s（快速）
- Context：128K tokens
- 成本：Flash 較 Pro 低約 3 倍

**深度思考（Reasoning）配置：**

DeepSeek V4 系列支援 reasoning tokens（深度思考模式），透過以下 Hermes 設定控制：

```bash
# 開啟深度思考
hermes config set model.reasoning true

# 設定思考強度（token 上限）
hermes config set model.max_reasoning_tokens 4096
```

**思考強度建議值：**

| 強度 | max_reasoning_tokens | 適用場景 |
|:----:|:-------------------:|----------|
| 低 | 1024 | 簡單分類、結構化輸出 |
| 中 | 4096 | 日常分析、程式除錯 |
| 高 | 8192 | 複雜推理、合約審查 |
| 全開 | 不設 | 最大品質（較慢） |

注意：`model.reasoning` 和 `model.max_reasoning_tokens` 為頂層設定，在 `config.yaml` 中位於 `model:` 區塊下，非 provider 層級。

**常見問題：**
1. **HTTP 401 認證失敗**: API key 無效或過期，請確認金鑰正確性
2. **HTTP 400 模型名稱錯誤**: 不要在 `model.default` 加 provider 前綴（如 `custom:deepseek/deepseek-v4-pro` 是錯誤的）
3. **resolver 找不到金鑰**: 使用 `custom:deepseek` 時確保金鑰在 `custom_providers` 列表中

### 4.1 Agnes AI 官方配置方式（與新版 Hermes 0.17+ 相容）

**推薦方式（官方建議）：**
```bash
hermes config set model.provider custom
hermes config set model.base_url https://apihub.agnes-ai.com/v1
hermes config set model.default agnes-2.0-flash
hermes config set model.api_key cpk-YOUR_KEY
```

**不推薦方式（舊版）：**
```bash
hermes config set providers.agnes.api_key sk-...      # ❌
hermes config set model.provider agnes                # ❌
```

**關鍵差異：**
- Base URL 只到 `/v1`，不要加 `/chat/completions`
- API Key 用 `model.api_key` 單獨配置，不走 `providers.*`
- Provider 名稱固定為 `custom`，不是 `agnes`

### 4.2 Agnes AI: API Key 類型與速度問題

**Key 類型：**
| Key 前綴 | 用戶類型 | 預期 RPM | 實際回應時間 |
|----------|---------|---------|-------------|
| `cpk-...` | Token Plan 付費用戶 | 1000 RPM | 6-10s（可能未被正確識別） |
| `sk-...` | 免費 / 默認 | 20 RPM | 6-10s |
| `sk-nous-...` | Nous Portal 產生的 key | 取決於綁定方案 | 可能 401 無法用於 Agnes API |

**問題根因：**
- 付費用戶的 `cpk-` key 可能未被後端正確識別為付費層
- 即使使用 `custom` provider，回應仍維持 6-7s
- 解決方向：向 Agnes 支援回報，或重設 key

**速度基準（實際測試）：**
| Provider | 回應時間 | 備註 |
|----------|---------|------|
| Agnes AI Token Plan | 6.68s | 異常，應 <3s |
| DeepSeek v4 Flash | 0.88s | ✅ 穩定快速 |
| OpenRouter (Ring-2.6-1T) | 待測試 | - |

### 4.3 Secret redactor hides true key length

Hermes redacts `sk-...` patterns in terminal output and `read_file`. A key displayed as `sk-I1G...kSbi` may actually be 51 chars, not 13. **Always verify with `len()` in Python:**

```python
cfg = open(os.path.expanduser('~/AppData/Local/hermes/config.yaml')).read()
import re
for m in re.finditer(r'^\s*api_key:\s*(\S+)', cfg, re.M):
    val = m.group(1)
    if val and val != "''":
        print(f"starts={val[:10]}... ends=...{val[-10:]} len={len(val)}")
```

### 4.4 `hermes config set` truncates if you type a truncated key
The redactor shows `sk-xxx...xxx` in output, which can trick you into writing truncated versions in subsequent commands. When setting keys, paste the **exact full string** from the user — or use a Python script to write directly to `config.yaml` / `auth.json`.

### 4.5 Credential pool keys share the same limit pool
Multiple keys of the **same access tier** (e.g. all Free-tier) share the provider's RPM limit. Creating more keys does not increase total capacity — rotation only helps avoid hitting per-key limits individually.

### 4.6 `hermes auth add custom` fails
The `custom` provider is not a recognized auth provider. Use `providers.<name>` in config.yaml instead.

### 4.7 Changes require `/reset` (including context_length)
Most model/provider config changes only take effect on a new session. In CLI: exit and relaunch. In gateway: `/restart`.

**context_length 特例：** 即使 config 中已設定 `context_length: 1000000`，session 啟動訊息仍顯示 `200K` 是常見情況。原因可能是：
- Session 是在 config 修改前啟動的，快照快取了舊值
- `~/.hermes/config.yaml` 的 `custom_providers.*.models.*.context_length` 與 `AppData\Local\hermes\config.yaml` 的 `model.context_length` 不一致

**修復：** 開新 session（`/new` 或 `hermes chat --model ...`），確認啟動 header 顯示正確的 context。

### 4.8 第三方設定檔的金鑰處理（`_FROM_ENV_` 模式）

第三方函式庫（如 mem0）需要從 JSON/YAML 讀取 API key，無法像 Hermes 一樣走 auth.json。

**解法 — 佔位符 + 執行期注入：**

```json
// mem0.json（磁碟上永遠不含有真實金鑰）
{
  "llm": {
    "config": { "api_key": "_FROM_ENV_DEEPSEEK_" }
  },
  "embedder": {
    "config": { "api_key": "_FROM_ENV_OPENROUTER_" }
  }
}
```

```python
# Python wrapper（執行時從環境變數注入）
def _inject_env_keys(cfg: dict) -> dict:
    key_map = {
        "_FROM_ENV_DEEPSEEK_": "DEEPSEEK_API_KEY",
        "_FROM_ENV_OPENROUTER_": "OPENROUTER_API_KEY",
    }
    for section in ["llm", "embedder"]:
        ak = cfg.get("oss", {}).get(section, {}).get("config", {}).get("api_key", "")
        if ak in key_map:
            cfg["oss"][section]["config"]["api_key"] = os.environ.get(key_map[ak], "")
    return cfg
```

**優點：**
- 設定檔磁碟上永遠不含有真實金鑰
- 執行時從環境變數注入，env var 只存在於行程記憶體
- 支援任意數量的第三方設定檔

### 4.9 Telegram Bot Token 不能透過 `hermes config set` 設定
`hermes config set telegram.bot_token` 會報錯 `Invalid environment variable name`。正確做法是直接寫入 `~/.hermes/.env`：
```bash
echo 'TELEGRAM_BOT_TOKEN="你的BOT_TOKEN"' >> ~/.hermes/.env
hermes gateway restart
```

### 4.10 Telegram Gateway 常見失敗原因
Gateway 顯示 "No messaging platforms enabled" 時，依序檢查：

| 步驟 | 檢查項目 | 解決方式 |
|------|---------|---------|
| 1 | `python-telegram-bot` 套件是否安裝 | `pip install python-telegram-bot`（裝在 Hermes venv） |
| 2 | `.env` 是否有 `TELEGRAM_BOT_TOKEN` | `echo 'TELEGRAM_BOT_TOKEN="..."' >> ~/.hermes/.env` |
| 3 | `GATEWAY_ALLOW_ALL_USERS` 是否設定 | `echo 'GATEWAY_ALLOW_ALL_USERS=true' >> ~/.hermes/.env` |
| 4 | `allowed_chats` 是否包含你的 chat_id | `hermes config set telegram.allowed_chats "你的ID"` |
| 5 | Gateway 是否重啟 | `hermes gateway restart` |
| 6 | 是否已對 bot 傳送 `/start` | 在 Telegram 搜尋 bot 名稱，傳 `/start` |

### 4.11 影片 API 的結果 URL 不在 `url` 欄位
Agnes Video API 完成回應中，實際 MP4 下載連結在 `remixed_from_video_id` 欄位，不是 `url` 也不是 `output.url`。查詢端點：
- ✅ 推薦: `GET /agnesapi?video_id=<ID>&model_name=agnes-video-v2.0`
- ❌ 不要用 `GET /v1/videos/<video_id>`（會 404）

### 4.13 Cronjob provider key 解析失敗

Cronjob session 載入 config.yaml 時，`«redacted:sk-…»` 遮罩值無法被解析為有效金鑰，導致錯誤 `Provider 'X' is set in config.yaml but no API key was found`。

**解法：建立 cronjob 時明確指定 model provider：**

```bash
cronjob(
    action="create",
    ...,
    model={"provider": "custom:deepseek", "model": "deepseek-v4-flash"},
)
```

使用 `custom:<name>` 格式（對應 `custom_providers` 列表中的條目），底層真實金鑰仍保留在原始配置中可被正確解析。不要依賴 default provider 推斷。

**注意：這個問題只在 cronjob session 中出現，一般對話 session 不受影響。**

### 4.14 模型名稱汰換：舊名停用前必須全部更新

**情境：** DeepSeek 2026-07-09 宣布 `deepseek-chat` 與 `deepseek-reasoner` 將於 2026-07-24 停止使用。

**鐵則：** 即使某個服務目前「沒有在用」，只要設定檔裡有舊模型名，就**必須更新**。

| 理由 | 說明 |
|:-----|:------|
| 定時任務 | cron job 可能觸發該服務，打到舊名 → 404 |
| 自動重啟 | systemd restart 後服務載入舊設定 → 炸 |
| 被動呼叫 | 其他服務可能透過內部網路呼叫它 |
| 複用 | 以後拿來測試時，第一個碰到就是舊名錯誤 |

**正確做法：** 掃描所有專案中的模型名稱，確認沒有殘留的即將停用名稱：

```bash
grep -r "deepseek-chat\|deepseek-reasoner" /opt/zhiyan-backend/ ~/.hermes/ --include="*.py" --include="*.yaml" --include="*.json" --include="*.env" 2>/dev/null
```

修完一個地方後，需要重啟服務（注意舊 process 可能還抓著 port）。

### 4.15 Custom provider credential pool 為空（即使主 provider 有 key）

**症狀：** cron job 使用 `custom:deepseek` provider 失敗，錯誤為 `HTTP 401: Authentication Fails, Your api key: ****ENV_ is invalid`。但主 `deepseek` provider 在一般對話中完全正常。

**根因：** `providers.deepseek` 和 `custom:deepseek` 在 `auth.json` 中各有獨立的 credential pool。設定 `providers.deepseek.api_key`（或 `_FROM_ENV_`）只會填充 `deepseek` pool，**不會自動同步**到 `custom:deepseek` pool。

```bash
# 診斷：檢查 credential pool 狀態
cat ~/.hermes/auth.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k, v in d.get('credential_pool', {}).items():
    print(f'{k}: {len(v)} credential(s)')
    for e in v:
        print(f'  source={e.get(\"source\")} id={e.get(\"id\")}')
"
# 預期輸出：
#   deepseek: 1 credential(s)          ← ✅ 有 key
#   custom:deepseek: 0 credential(s)   ← ❌ 空的！
```

**修復：** 直接將 credential 加入 `custom:deepseek` pool，沿用環境變數來源（不硬編碼金鑰）：

```bash
python3 -c "
import json, uuid
from datetime import datetime, timezone

with open('/home/ysga1/.hermes/auth.json') as f:
    data = json.load(f)

ds_pool = data['credential_pool'].get('deepseek', [])
if not ds_pool:
    print('ERROR: main deepseek pool is also empty')
    exit(1)

ref = ds_pool[0]
entry = {
    'id': 'ds-' + uuid.uuid4().hex[:6],
    'label': ref.get('label', 'DEEPSEEK_API_KEY (custom)'),
    'auth_type': ref.get('auth_type', 'api_key'),
    'priority': 0,
    'source': ref.get('source', 'env:DEEPSEEK_API_KEY'),
    'last_status': None,
    'last_status_at': None,
    'last_error_code': None,
    'last_error_reason': None,
    'last_error_message': None,
    'last_error_reset_at': None,
    'base_url': ref.get('base_url', 'https://api.deepseek.com/v1'),
    'request_count': 0,
    'secret_fingerprint': None
}
data['credential_pool'].setdefault('custom:deepseek', []).append(entry)
data['updated_at'] = datetime.now(timezone.utc).isoformat()
with open('/home/ysga1/.hermes/auth.json', 'w') as f:
    json.dump(data, f, indent=2)
print('OK - added credential to custom:deepseek pool')
"

# 驗證
cat ~/.hermes/auth.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
pool = d['credential_pool'].get('custom:deepseek', [])
print(f'custom:deepseek pool: {len(pool)} credential(s)')
for e in pool:
    print(f'  source={e.get(\"source\")} id={e.get(\"id\")}')
"
```

**為什麼不直接用 `hermes config set`？** Hermes CLI 不支援 `custom:deepseek` 這種格式的 provider 名稱來設定金鑰。必須直接編輯 `auth.json`。

**預防：** 建立 cron job 時，如果它使用 `custom:<name>` provider，先確認 credential pool 不為空：

```bash
python3 -c "
import json
with open('/home/ysga1/.hermes/auth.json') as f:
    d = json.load(f)
pool = d.get('credential_pool', {}).get('custom:deepseek', [])
print('OK' if pool else 'EMPTY - will fail at runtime')
"
```

### 4.16 Credential pool `env:` source not resolved at runtime (cron fallback)

**症狀：** 即使已按照 4.15 將 credential 加入 `custom:deepseek` pool（source 設為 `env:DEEPSEEK_API_KEY`），cron job 執行時仍報 `401 Authentication Fails`，錯誤訊息顯示金鑰值為 `****ENV_` — 表示 `env:` 變數在 cron session 啟動時未被解析為實際值。

**根因：** Cron job session 的環境變數載入時機與正常對話 session 不同。`auth.json` 中 `source: "env:DEEPSEEK_API_KEY"` 的 credential 在 cron 啟動時無法被正確解析，導致傳出空字串金鑰。

**修復策略（二選一，後者為最終可靠方案）：**

**策略 A：不要用 `custom:<name>`，改用主 provider**

將 cron job 的 model provider 從 `custom:deepseek` 改為 `deepseek`（主 provider）。主 provider 的金鑰直接在 config.yaml 中，不經過 credential pool 解析：

```python
# 在建立或更新 cron job 時指定
cronjob(
    action="update",
    job_id="...",
    model={"provider": "deepseek", "model": "deepseek-v4-flash"},
)
```

> **為什麼策略 A 有效：** 主 provider (e.g. `deepseek`) 的金鑰直接寫在 `config.yaml` 的 `providers.deepseek.api_key` 中，cron job session 載入 config.yaml 時直接讀取。而 `custom:deepseek` 的金鑰存在 `auth.json` 的 credential pool 中，其 `source: "env:DEEPSEEK_API_KEY"` 在 cron session 中無法被解析為實際環境變數值。

**策略 B：在 cron job fallback 的 provider 鏈中將 `custom:deepseek` 排在主 provider 之後**

```python
cronjob(
    action="update",
    job_id="...",
    model={"provider": "deepseek", "model": "deepseek-v4-flash"},
    # 不指定 custom:deepseek，讓 cron 使用主 provider
)
```

**推薦策略 A** — 最簡單、最穩定。

**診斷：確認問題是否為 env 解析失敗**

```bash
# 如果 cron job 錯誤訊息包含 '****ENV_' 或類似遮罩值作為金鑰
# 代表 env 變數未被解析，此時改策略 A
# 如果錯誤是單純的 401，可能是金鑰本身過期
```

```bash
---

## 5. Verification

```bash
# Quick test
hermes chat -q "Respond with: OK" --provider custom --model model-name

# List credential pool
hermes auth list

# Check stored key lengths
python3 -c "
import re, os
c = open(os.path.expanduser('~/AppData/Local/hermes/config.yaml')).read()
for m in re.finditer(r'^\\s*api_key:\\s*(\\S+)', c, re.M):
    v = m.group(1)
    if v and v != \"''\": print(f'{v[:10]}...{v[-10:]} len={len(v)}')
"
```

---
---
## 7. VS Code Copilot BYOK (Bring Your Own Key)

When the user wants to use a custom OpenAI-compatible provider (e.g., Agnes AI) inside VS Code's Copilot Chat:

### 7.1 Current Status (as of VS Code 1.126 / Copilot Chat 0.54)

- `github.copilot.chat.customOAIModels` is **DEPRECATED** — do NOT use this setting anymore.
- The replacement is **Custom Endpoint** provider (currently Insiders-only as of Oct 2025).
- For stable VS Code releases, BYOK for custom OpenAI-compatible endpoints is **not yet available** — users must use the UI flow.

### 7.2 Recommended Approach: Manual UI Setup

Guide the user to set up via VS Code's **Manage Language Models** UI:

1. VS Code `Ctrl+Shift+P` → `Chat: Manage Language Models`
2. `Add Models` → `Custom Endpoint` (or `OpenAI` if Custom Endpoint is unavailable)
3. Fill in:
   - **Group Name**: provider name (e.g., `Agnes AI`)
   - **Display Name**: model display name (e.g., `Agnes Flash`)
   - **API Key**: the full API key
   - **API Base URL**: e.g., `https://apihub.agnes-ai.com/v1`
   - **API Type**: `chat-completions` (OpenAI-compatible) or `messages` (Anthropic-compatible)
4. Save and select the model in the Chat panel's model picker

### 7.3 Verification Steps

Before guiding the user, verify the API key works:
```bash
# Quick connectivity test
curl -s https://apihub.agnes-ai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY" | python3 -m json.tool

# Chat completion test
python3 -c "
import urllib.request, json
key = 'YOUR_KEY'
data = json.dumps({'model': 'agnes-2.0-flash', 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 10}).encode()
req = urllib.request.Request('https://apihub.agnes-ai.com/v1/chat/completions', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {key}')
resp = urllib.request.urlopen(req, timeout=10)
print(json.loads(resp.read())['choices'][0]['message']['content'])
"
```

### 7.4 Pitfalls

- **Don't write `settings.json` for BYOK** — the `env` block or `customOAIModels` in settings.json is either ignored or deprecated. Always guide the user to the UI.
- **Copilot CLI needs a separate key** — `gh copilot` uses a Fine-grained PAT with "Copilot Requests" permission, NOT the same as the OpenAI-compatible API key.
- **Free tier RPM applies** — Agnes AI free tier has 20 RPM shared across all keys. The user should be aware of rate limits.
- **VS Code version matters** — Custom Endpoint provider may require VS Code Insiders. Check version with `code --version` before suggesting the feature.
- **BYOK doesn't cover completions** — BYOK only works for Chat and Utility Tasks. Inline Suggestions (Completions) still require a GitHub Copilot subscription.

---

## 6. Parallel Sub-Agent Workflow（子代理平行任務）

**當用戶問為什麼不用子代理時，請立即修正，不要等下一回合。**

用戶明確要求優先使用 `delegate_task` 的 `tasks` 陣列進行平行作業，而不是序列化一個接一個做。

### 6.1 何時使用

| 情境 | 序列化 ❌ | 平行子代理 ✅ |
|------|----------|-------------|
| 生成 5 張圖片 | 逐一呼叫 API，5x 時間 | `delegate_task(tasks=[...])`，一次全部送出 |
| 圖片→影片轉換 | 等第一張完成→送第一支→等第二張... | 同時提交所有影片任務 |
| 多方研究 | 逐篇讀取 | 分散給 5 個子代理同時搜尋 |
| 程式碼+測試 | 先寫程式再寫測試 | 一個子代理寫程式，另一個同時規劃測試 |
| 系統掃描 | `PATH`→`pip`→`npm`→`desktop` 逐項 | 多個子代理各掃一類 |

### 6.2 平行批次模式

```python
# 好的做法：tasks 陣列平行送出
delegate_task(tasks=[
    {"goal": "任務A", "toolsets": ["terminal"]},
    {"goal": "任務B", "toolsets": ["web"]},
    {"goal": "任務C", "toolsets": ["terminal", "file"]},
])

# 不好的做法：一個做完再做下一個
result_a = some_task()    # ❌ 浪費時間
result_b = another_task() # ❌ 
result_c = yet_another()  # ❌
```

### 6.3 可用的子代理工具（本機已安裝）

| 工具 | 路徑 | 版本 | 用途 |
|------|------|------|------|
| `claude` | `~/.local/bin/claude` | 2.1.159 | Anthropic coding agent |
| `opencode` | PATH 內 | 1.17.11 | Open-source coding agent |
| `copilot` | VS Code Copilot CLI | 1.0.63 | GitHub AI CLI |
| `ollama` | AppData/Local/Programs/Ollama | 0.23.2 | Local LLM |
| `hermes` | venv/Scripts/hermes | 0.17.0 | Self |

**注意：** `@openai/codex` (v0.133.0) 已安裝但需 GPT 付費，使用者無付費方案時不可用。

### 6.4 平行媒體管線（Image + Video Pipeline）

對於圖片→影片的動畫工作流：

```
Phase 1: delegate_task 5 個子代理 → 平行生成 5 張場景圖片
Phase 2: 收集所有圖片 URL → 平行送出 video API 任務
Phase 3: 平行輪詢所有影片結果
```

**已知限制：**
- Agnes 圖生影 API：`image` 參數需要**公開 URL**，不接受 Base64 data URI
- 影片結果 URL 在 `remixed_from_video_id` 欄位（不是 `url`）
- 查詢端點用 `GET /agnesapi?video_id=<ID>&model_name=agnes-video-v2.0`
- 幀數規則：`8n+1`，最大值 441

---

## 8. Reference Files

- `references/agnes-ai-integration.md` — Full Agnes AI provider setup from this session: model specs, free tier limits, sub-agent key separation.
- `references/vscode-copilot-byok-setup.md` — VS Code Copilot BYOK configuration guide, deprecated vs current settings, troubleshooting.
- `references/multi-provider-routing-strategy.md` — Multi-provider routing strategy (Agnes + DeepSeek): tiered stack, specialist routing, fallback consensus, cache optimization. Includes Python router skeleton and risk matrix. Use when the user asks to combine multiple API providers in production.
- `references/hermes-context-config.md` — Hermes context length 設定排查：雙 config 檔案衝突、session 快照行為、修復步驟。當 session 顯示的 context 與 config 設定不符時查閱。
- `references/deepseek-api-quickref.md` — DeepSeek API 配置速查表：快速配置命令、模型切換、常見錯誤排查、實測數據。
- `references/env-key-management.md` — 全系統金鑰位置盤點：2026-07-09 實戰記錄，哪些檔案可以放 key、哪些不行。
