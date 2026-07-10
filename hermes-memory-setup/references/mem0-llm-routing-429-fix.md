# Mem0 LLM Extraction 429 修復紀錄

## 問題

Mem0 的 LLM extraction（從記憶中提取結構化事實）持續噴 429：

```
ERROR mem0.memory.main: LLM extraction failed: Error code: 429
All models exhausted: 2 routes checked (2 rate-limited or on cooldown)
```

## 根因

`mem0.json` 中的 LLM extraction 配置指向 **FreeLLM API**（`http://localhost:3001/v1`），而非直接連接 upstream provider：

```json
{
  "llm": {
    "provider": "openai",
    "config": {
      "model": "deepseek-v4-flash",
      "openai_base_url": "http://localhost:3001/v1",  // ← FreeLLM router
      "api_key": "freellmapi-..."
    }
  }
}
```

FreeLLM 作為多 upstream 路由器，當其上游全被 rate limit 時回傳 429。Mem0 無 retry 邏輯，直接失敗。

## 修復

將 `openai_base_url` 改為 upstream 的**直接 API 端點**，繞過 FreeLLM：

```json
{
  "llm": {
    "provider": "openai",
    "config": {
      "model": "deepseek-v4-flash",
      "openai_base_url": "https://api.deepseek.com/v1",  // ← 直連 DeepSeek
      "api_key": "sk-..."  // ← DeepSeek API key
    }
  }
}
```

## 金鑰隔離（進階）

為避免 `api_key` 以明文存在 `mem0.json` 中：

1. `mem0.json` 放佔位符：`"_FROM_ENV_DEEPSEEK_"`
2. 在 Python wrapper 中從 `os.environ` 注入真實 key：

```python
def _inject_env_keys(cfg: dict) -> dict:
    key_map = {"_FROM_ENV_DEEPSEEK_": "DEEPSEEK_API_KEY"}
    for section in ["llm", "embedder"]:
        ak = cfg.get("oss", {}).get(section, {}).get("config", {}).get("api_key", "")
        if ak in key_map:
            cfg["oss"][section]["config"]["api_key"] = os.environ[key_map[ak]]
    return cfg
```

## 驗證

```bash
cd /home/ysga1/zhiyan-search && python3 save_summary_to_mem0.py --dry-run
# 不再出現 429
```

## 相關

- `save_summary_to_mem0.py` 中的 `_inject_env_keys()` 函式
- `hermes-custom-providers` skill — 金鑰隔離鐵律
