# Mini-App 儀表板狀態產生器

## 用途

`miniapp-status.py` 是輕量系統健康探針，每 15 分鐘透過 cron 更新靜態 JSON 檔，供 Tg Mini App 儀表板讀取。

## 安裝位置

```
~/.hermes/scripts/miniapp-status.py    → cron 每15分鐘執行
/usr/local/bin/miniapp-gen.py          → sudo 版本（寫入 /var/www/）
```

## 部署 cron

```bash
(crontab -l 2>/dev/null | grep -v miniapp-gen; \
 echo "*/15 * * * * sudo python3 /usr/local/bin/miniapp-gen.py >/dev/null 2>&1") | crontab -
```

## 監控資料

| 數據源 | 欄位 | 取得方式 |
|:-------|:------|:---------|
| OpenRouter 額度 | `openrouter.total_credits / usage / remaining` | `GET /api/v1/credits` |
| 服務健康 | `services[].name / status` | `curl` 各 localhost port |
| Groq 配額 | `groq[].key / limit / used` | FreeLLM DB `provider_quota_state` |
| 每日用量 | `daily[].day / tokens` | FreeLLM DB `requests` |
