---
name: model-routing-strategy
description: FreeLLM API 路由配置、用量分析、Embedding 修復與平台金鑰審計
status: stable
---

# 🔀 模型路由與顧問策略

## 功用

多模型路由策略設定，根據任務類型、成本與品質需求自動選擇最佳模型。涵蓋 FreeLLM API（本機 LLM 代理網關）的配置審計、用量分析、金鑰審計與 Embedding 路由修復。

---

## 路由原則（客戶端層）

| 任務等級 | 目標模型 | 情境 |
|:---------|:---------|:------|
| 簡單 | 低成本模型（free 路由） | 摘要、翻譯、簡答 |
| 一般 | 平衡模型 | 分析、整理 |
| 複雜 | 高品質模型 | 法律研究、推理 |
| 關鍵 | 旗艦模型（Pro） | 最終產出、審計 |

---

## FreeLLM API 路由機制（伺服器層）

### 配置檢查

```bash
sudo sqlite3 /var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db \
  "SELECT key, value FROM settings WHERE key IN ('routing_strategy', 'active_profile_id');"
```

| 設定 | 值 | 意義 |
|:-----|:---|:------|
| `routing_strategy` | `auto` | 自動錯誤切換 + 依 profile 優先級路由（2026-07-07 從 smartest 改為 auto） |
| `active_profile_id` | 1 | 當前生效的 Profile |

### Profile 優先級（手動路由用）

Profile 內模型依 `priority` 排序（數字越小越優先）：

```sql
SELECT m.model_id, m.platform, pm.priority, m.intelligence_rank, m.paid_input_per_m
FROM profile_models pm
JOIN models m ON m.id = pm.model_db_id
WHERE pm.profile_id = 1
ORDER BY pm.priority ASC;
```

### 🔄 `smartest` → `auto` 遷移（2026-07-07）

`smartest` 路由策略的問題：
- 繞過 Profile 優先級，直接以 intelligence_rank 選模型
- 付費版與免費版同模型時，傾向選付費版（rank 較高）
- 不處理錯誤回退 — 選中模型若 429 或 timeout，直接失敗而非往下換

`auto` 策略的行為：
- 依 Profile 優先級順序嘗試（2026-07-07 已重排：Groq 1-7，OpenRouter free 8+）
- 若當前模型返回錯誤（429/timeout/503），**自動切換到下一個優先級模型**
- 直到找到可用模型或窮舉完畢
- 等同於「智慧化錯誤切換 + profile 優先級路由」

```bash
# 切換指令
DB="/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db"
sudo sqlite3 "$DB" "UPDATE settings SET value='auto' WHERE key='routing_strategy';"
```

### Groq 路由優先級（2026-07-07 設定）

Profile 1 已重排，Groq 模型佔據前 7 名。**Groq 最多支援 50 把獨立金鑰**，每把擁有各自獨立的 FREE tier 配額（30 RPM、70K TPM、6-15M TPD 依模型而定），互不影響：

```sql
SELECT f.id, f.priority, m.model_id, m.platform
FROM fallback_config f
JOIN models m ON f.model_db_id = m.id
WHERE f.enabled = 1
ORDER BY f.priority ASC;
```

---

## 用量分析

### 各模型 Token 耗用排行

```bash
DB="/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db"
sudo sqlite3 -column -header "$DB" "
SELECT
  model_id,
  COUNT(*) AS calls,
  SUM(input_tokens) AS total_input,
  SUM(output_tokens) AS total_output,
  SUM(input_tokens + output_tokens) AS total_tokens,
  ROUND(AVG(latency_ms)) AS avg_latency_ms,
  ROUND(SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS error_pct
FROM requests
GROUP BY model_id
ORDER BY total_tokens DESC
LIMIT 20;
"
```

### 每日用量趨勢

```sql
SELECT DATE(created_at) AS day,
       COUNT(*) AS calls,
       SUM(input_tokens + output_tokens) AS total_tokens
FROM requests
WHERE created_at >= DATE('now', '-7 days')
GROUP BY day
ORDER BY day DESC;
```

---

## Embedding 路由修復

### 問題

FreeLLM API 的 `embedding_models` 表控制 Embedding 模型的選取順序。當預設 family 的 GitHub 路由被 429 打死時，Mem0 和 ChromaDB 的語意搜尋會全部癱瘓。

### 檢查 Embedding 路由

```sql
-- 檢查當前所有 embedding 模型及其優先級
SELECT id, family, platform, model_id, dimensions, priority, quota_label
FROM embedding_models
ORDER BY priority, id;

-- 檢查預設 family
SELECT key, value FROM settings WHERE key='embeddings_default_family';
```

### 解決方案矩陣

| 方案 | 作法 | 維度 | 成本 | 適用 |
|:-----|:------|:----:|:----:|:-----|
| **A. OpenRouter 直連**（推薦） | Mem0 embedder 改走 OpenRouter API，保留 text-embedding-3-small | **1536** | $0.02/1M tokens | Qdrant 相容，舊記憶不損 |
| **B. NVIDIA Nemotron** | FreeLLM 路由改走 nvidia/llama-nemotron-embed-vl-1b-v2 | 2048 | 免費 40 RPM | 需重建 ChromaDB index |
| **C. 自託管 freely.py** | 本機 HuggingFace Inference API 跑 bge-m3 | 1024 | 免費（需 HF token） | 完全自主，但需啟動服務 |

### Mem0 Embedding 配置路徑

當方案 A 啟用時，Mem0 的 embedder 指向 OpenRouter：

```bash
# mem0.json embedder config
{
  "model": "text-embedding-3-small",
  "openai_base_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-or-v1-...",
  "embedding_dims": 1536
}
```

---

## Mem0 LLM Extraction 路由陷阱（2026-07-09 修復）

### 問題

Mem0 的 `mem0.json` 中，LLM extraction 若將 `openai_base_url` 設為 FreeLLM（`http://localhost:3001/v1`），會導致：

```
ERROR mem0.memory.main: LLM extraction failed: Error code: 429
All models exhausted: 2 routes checked (2 rate-limited or on cooldown)
```

**根因：** Mem0 的 LLM extraction 需要一個穩定、低延遲的 LLM 來處理記憶提取。FreeLLM 路由會經過多層上游，只要上游有任一環 rate limited，整個 extraction 就失敗。這會導致：
- 跨 session 記憶無法同步（Mem0 不寫入新記憶）
- STRATA 自動壓縮周期雖然寫入 MEMORY.md，但 Mem0 向量同步失敗
- 使用者感覺系統「不記得」之前的事

### 診斷

```bash
# 檢查 mem0.json 中的 LLM 路由
cat ~/.hermes/mem0.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['oss']['llm']['config']['openai_base_url'])"

# 檢查 Mem0 日誌中的 429 錯誤
journalctl --user -u hermes-gateway --no-pager -n 50 2>/dev/null | grep -i "mem0.*429\|LLM extraction failed"
```

### 正確配置：DeepSeek 直連

```json
{
  "llm": {
    "provider": "openai",
    "config": {
      "model": "deepseek-v4-flash",
      "openai_base_url": "https://api.deepseek.com/v1",
      "api_key": "_FROM_ENV_DEEPSEEK_"
    }
  }
}
```

注意：
- 改為 DeepSeek 直連（不走 FreeLLM 路由）
- `api_key` 使用 `_FROM_ENV_` 佔位符（見 `hermes-custom-providers` 技能的 pitfall 4.8）
- 配合 `save_summary_to_mem0.py` 的環境變數注入

### 驗證修復

```bash
python3 ~/zhiyan-search/save_summary_to_mem0.py --dry-run
# 不應出現 429 錯誤
```

### Embedding 路由優先級設定

在 FreeLLM DB 中調整 `embedding_models` 表的 `priority` 來控制 fallback 鏈：

| 優先級 | 模型 | 平台 | 維度 | 配額 |
|:------:|:-----|:-----|:----:|:-----|
| 1 (最優先) | NVIDIA Nemotron Embed VL | nvidia | 2048 | 40 RPM 免費 |
| 1 | Cloudflare BGE-M3/Qwen3 | cloudflare | 1024 | 10K/天 |
| 5 | Google Gemini Embedding | google | 3072 | degrated (quota hit) |
| 100 (最低) | text-embedding-3-small | github | 1536 | 429 dead |

---

## OpenRouter 金鑰管理

### OpenRouter 金鑰格式

所有 OpenRouter API key 以 `sk-or-v1-` 開頭。

### 金鑰儲存

```bash
# 存於 ~/.hermes/env/openrouter.env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
chmod 600 ~/.hermes/env/openrouter.env
```

### 餘額查詢

```bash
curl -s https://openrouter.ai/api/v1/credits \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
# 回傳: {"data":{"total_credits":5,"total_usage":0.78}}
# 剩餘 = total_credits - total_usage
# 注意: total_credits 是累計儲值額，非當前限額

# 用量明細
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
# → usage, usage_daily, usage_weekly, usage_monthly, is_free_tier, limit, limit_remaining

# 速率限制
curl -s https://openrouter.ai/api/v1/limits
```

### OpenRouter Embedding 支援

OpenRouter 的 `/v1/embeddings` 端點完全 OpenAI 相容。支援 `text-embedding-3-small`（1536 維，Provider: OpenAI）、`text-embedding-3-large`（3076 維）。成本極低（~$0.02/1M tokens）。

---

## 真實付費狀態：全部免費

### 關鍵認知：catalog 標價 ≠ 實際付費

FreeLLM API 的 `paid_input_per_m` / `paid_output_per_m` 欄位是**上游 catalog metadata**（從模型提供者端抓取的公開標價），不是實際收費。

```sql
-- 查所有啟用中的平台金鑰
SELECT id, platform, label, status, enabled FROM api_keys WHERE enabled=1 ORDER BY platform;

-- 查各平台 free tier 配額
SELECT platform, monthly_token_budget, COUNT(*) AS models
FROM models WHERE monthly_token_budget != ''
GROUP BY platform, monthly_token_budget ORDER BY platform;
```

| 平台 | 金鑰類型 | 配額限制 | 實際付費？ |
|:-----|:---------|:---------|:----------|
| NVIDIA | Developer 免費帳號 | `free · 40 RPM` | ❌ |
| Mistral | 開發者免費層 | ~50-100M tokens/月 | ❌ |
| Groq | 免費層 | ~6-15M tokens/月 / 最多 **50 把獨立金鑰** | ❌ |
| Google | AI Studio 免費層 | ~3-30M tokens/月 | ❌ |
| GitHub | GitHub Models 免費 | ~9M tokens/月 | ❌ |
| OpenRouter | 免費路由 | ~6-120M tokens/月 | ❌ |
| Cerebras / Cloudflare / Cohere / LLM7 | 開發者免費試用 | 各自配額 | ❌ |

---

## 配額檢查工作流

### 即時配額查詢

```bash
DB="/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db"

# 查所有平台最新剩餘配額
sudo sqlite3 -column -header "$DB" "
SELECT 
  pqs.platform,
  pqs.quota_pool_key,
  pqs.metric,
  pqs.limit_value,
  pqs.remaining_value,
  pqs.status_code,
  pqs.reset_at,
  pqs.confidence,
  pqs.notes
FROM provider_quota_state pqs
WHERE pqs.limit_value > 0
ORDER BY 
  CASE WHEN pqs.remaining_value IS NULL THEN 0 ELSE pqs.remaining_value * 1.0 / pqs.limit_value END ASC;
"

# 查近期 429 / rate limit 錯誤（按模型）
sudo sqlite3 -column -header "$DB" "
SELECT model_id, error, COUNT(*) as count
FROM requests
WHERE (error LIKE '%429%' OR error LIKE '%quota%' OR error LIKE '%ResourceExhausted%' OR error LIKE '%rate%')
  AND status != 'success'
  AND created_at >= datetime('now', '-3 days')
GROUP BY model_id, error
ORDER BY count DESC
LIMIT 20;
"
```

### 配額儀表板範本

當用戶問「剩餘配額」時，按以下結構輸出儀表板：

```
## 📊 各平台剩餘配額儀表板

### 🟢 健康 — 還有餘裕
| 平台 | 配額類型 | 使用/限制 | 狀態 |

### 🟡 逼近上限
| 平台 | 問題 | 次數 |

### 🔴 已滿／頻繁被限
| 平台 | 錯誤類型 | 次數 | 影響 |
```

**燈號規則：**
- 🟢 = remaining > 50% 或 error free
- 🟡 = remaining 10~50% 或 sporadic errors
- 🔴 = remaining < 10% 或 frequent 429/503

### 常見配額問題診斷

| 徵兆 | 可能原因 | 檢查方式 |
|:-----|:---------|:---------|
| Embedding 全部 429 | GitHub 免費路由超限（text-embedding-3-small） | `WHERE error LIKE '%429%' AND model_id LIKE '%embedding%'` |
| NVIDIA "Worker limit" | 免費帳號並發上限 32 | `WHERE error LIKE '%ResourceExhausted%'` |
| Google "Quota exceeded" | AI Studio 免費額度用完 | `WHERE error LIKE '%quota%' AND platform='google'` |
| OpenRouter free limit | 每日免費模型額度 (1000 req) 用完 | `WHERE error LIKE '%free-models-per-day%'` |

---

## DB Schema 參考

```
/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db
```

| 表格 | 用途 |
|:-----|:------|
| `requests` | 每次 API 呼叫記錄（model, tokens, latency, status） |
| `request_hourly` | 逐時彙總 |
| `models` | 模型目錄（platform, intelligence_rank, 標價, 配額） |
| `api_keys` | 金鑰設定（platform, status, base_url） |
| `embedding_models` | Embedding 模型路由表（family, platform, dims, priority） |
| `profiles` | Profile 定義 |
| `profile_models` | Profile 內模型優先級 |
| `settings` | 全域設定（routing_strategy, active_profile_id, embeddings_default_family） |
| `fallback_config` | 容錯回退設定 |
| `users` | 管理員帳號 |

---

## 路由策略調整方案

| 方案 | 做法 | 效果 |
|:-----|:------|:------|
| **A. 免費優先 Profile** | `:free` 模型優先級排前、付費版降級或禁用 | 自動路由優先走免費 |
| **B. 雙 Profile** | Profile 1 = 免費優先 / Profile 2 = 旗艦付費 | 手動切換控制 |
| **C. 客戶端指定** | 客戶端（Hermes）強制指定 `:free` 模型 | 從源頭掐斷付費路由 |
| **D. Groq Key Rotation**（2026-07-07 新增） | 利用 Groq 支援最多 50 把獨立金鑰的特性，建立金鑰輪換池。每把金鑰有各自獨立的 30 RPM / 70K TPM 配額。可透過 Mini App 儀表板的 `/api/keys/add` 端點即時新增。 | 繞過單把金鑰 rate limit，放大免費容量最高 50 倍 |

### Groq 路由優先級（2026-07-07 設定）

Profile 1 已重排，Groq 模型佔據前 7 名：

```sql
-- 2026-07-07 最終設定
UPDATE profile_models SET priority = 1 WHERE model_db_id = 52;   -- openai/gpt-oss-120b (groq)
UPDATE profile_models SET priority = 2 WHERE model_db_id = 55;   -- llama-3.1-8b-instant (groq)
UPDATE profile_models SET priority = 3 WHERE model_db_id = 17;   -- llama-3.3-70b-versatile (groq)
UPDATE profile_models SET priority = 4 WHERE model_db_id = 106;  -- groq/compound (groq)
UPDATE profile_models SET priority = 5 WHERE model_db_id = 107;  -- groq/compound-mini (groq)
UPDATE profile_models SET priority = 6 WHERE model_db_id = 53;   -- openai/gpt-oss-20b (groq)
UPDATE profile_models SET priority = 7 WHERE model_db_id = 119;  -- openai/gpt-oss-safeguard-20b (groq)
```

### Groq Key Rotation 實作

```bash
# 1. 手動新增金鑰（透過 Mini App 儀表板）
POST /api/keys/add
{"key": "gsk_xxxxx", "label": "groq-key-7"}

# 2. 金鑰會寫入 ~/.hermes/env/groq-<label>.env
# 3. 後續需手動加入 FreeLLM API（DB 加密限制）

# 查詢目前已知 Groq 配額
sudo sqlite3 "$DB" "
SELECT ak.id, q.metric, q.limit_value, q.remaining_value
FROM provider_quota_state q
JOIN api_keys ak ON q.key_id=ak.id
WHERE ak.platform='groq' AND q.limit_value>0
ORDER BY q.observed_at DESC;
"
```

---

## 參考資料

- **Groq 模型詳解**: `references/groq-models.md` — 7 個 Groq 模型的功用、限額、價格與任務推薦
- **Groq 生態研究**: `references/groq-ecosystem.md` — LPU 架構、社群評價、SLA、比較
- 原檔: 知識庫/🔧代理管理/🔀 模型路由與顧問策略.md