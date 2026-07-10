# Mini App Watchdog 實例

Session 日期：2026-07-08  
伺服器路徑：`/usr/local/bin/miniapp-server.py`  
Port：`8081`  
觸發原因：伺服器無預警死亡，無 crash log

## 最終腳本

路徑：`~/.hermes/scripts/miniapp-watchdog.sh`

```bash
#!/bin/bash
MINIAPP_SCRIPT="/usr/local/bin/miniapp-server.py"
PORT="8081"

if pgrep -f "$MINIAPP_SCRIPT" > /dev/null; then
  if ss -tlnp | grep -q ":$PORT "; then
    exit 0
  fi
  sudo pkill -f "$MINIAPP_SCRIPT" 2>/dev/null
  echo "⚠️ Mini App 進程僵死（port $PORT 未監聽），已終止等待重啟"
else
  echo "⚠️ Mini App 進程已死亡（port $PORT）"
fi

python3 "$MINIAPP_SCRIPT" "$PORT" &
sleep 2

if pgrep -f "$MINIAPP_SCRIPT" > /dev/null && ss -tlnp | grep -q ":$PORT "; then
  echo "✅ Mini App 已自動恢復於 port $PORT ($(date '+%H:%M:%S'))"
else
  echo "❌ Mini App 重啟失敗！請手動介入"
fi
```

## Cronjob 設定

- 排程：`*/5 * * * *`
- 模式：`no_agent=true`（純腳本，零 token 消耗）
- 投遞：`origin`（回 TG 對話）
- 正常時靜默（stdout 空），異常時自動發送重啟通知

## 健康狀態解讀

| stdout 輸出 | 意義 |
|---|---|
| 無輸出 | ✅ 一切正常 |
| ⚠️ 進程死亡/僵死... → ✅ 已自動恢復 | 自動修復成功 |
| ❌ 重啟失敗 | 需手動介入 |

## 手動維護指令

```bash
# 檢查上次執行狀態
cronjob action=list

# 立即執行一次測試
cronjob action=run job_id=<id>

# 查詢排程（確認下次執行時間）
cronjob action=list

# 停用（不再自動檢查）
cronjob action=pause job_id=<id>

# 重新啟用
cronjob action=resume job_id=<id>
```
