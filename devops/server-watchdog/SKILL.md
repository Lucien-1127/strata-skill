---
title: server-watchdog
name: server-watchdog
description: 使用 Hermes cronjob + no_agent 腳本建立伺服器程序 Watchdog — 零 token 消耗、自動偵測死亡/僵死並重啟，僅在異常時通知
tags: [cronjob, watchdog, healthcheck, no-agent, server, monitoring]
version: 1.0
---

# Server Watchdog

建立一個免 LLM 參與的輕量 Watchdog 定時檢查伺服器進程存活。正常時零通知、零 token 消耗；異常時自動重啟並發送警示。

## 何時使用

- 背景伺服器進程（Flask、Node.js、Python HTTP server 等）會無預警死亡
- 進程尚在但 port 已不監聽（僵死 zombie 狀態）
- 需要自動恢復但不想浪費 token 跑完整 LLM 循環
- 任何「檢查 → 重啟 → 驗證」的自動化流程

## 快速參考架構

```
shell script (*.sh) → cronjob(no_agent=True) → 自動執行並投遞 stdout
```

| 元件 | 角色 |
|---|---|
| `.hermes/scripts/<name>.sh` | 實際檢查+重啟邏輯 |
| `cronjob(action=create, no_agent=true)` | 定時驅動，零 token |
| stdout 輸出 | 空=正常靜默；非空=異常警報投遞 |

## 標準 Watchdog 腳本模板

```bash
# 通用模板 — 修改 PROCESS_NAME 與 PORT 即可復用

PROCESS_NAME="/path/to/your/server.py"   # ⬅️ 改這裡
PORT="8081"                                # ⬅️ 改這裡

# Step 1: 檢查進程
if pgrep -f "$PROCESS_NAME" > /dev/null; then
  # Step 1a: 進程活著，再檢查 port 監聽
  if ss -tlnp | grep -q ":$PORT "; then
    exit 0  # 一切正常 → 靜默
  fi
  # 進程在但 port 沒監聽 → zombie
  sudo pkill -f "$PROCESS_NAME" 2>/dev/null
  echo "⚠️ 進程僵死（port $PORT 未監聽），已終止"
else
  echo "⚠️ 進程已死亡（port $PORT）"
fi

# Step 2: 重啟
python3 "$PROCESS_NAME" "$PORT" &
sleep 2

# Step 3: 驗證
if pgrep -f "$PROCESS_NAME" > /dev/null && ss -tlnp | grep -q ":$PORT "; then
  echo "✅ 已自動恢復於 port $PORT ($(date '+%H:%M:%S'))"
else
  echo "❌ 重啟失敗！請手動介入"
fi
```

## 設定步驟

### 1. 建立腳本

```bash
mkdir -p ~/.hermes/scripts
# 用 write_file 寫入腳本內容
chmod +x ~/.hermes/scripts/watchdog.sh
```

### 2. 建立 cronjob

```bash
cronjob action=create \
  name="服務 Watchdog" \
  schedule="*/5 * * * *" \
  script=watchdog.sh \
  no_agent=true
```

### 3. 測試一次

```bash
cronjob action=run job_id=<id>
```

## 排程頻率建議

| 間隔 | 適用場景 |
|---|---|
| `*/1 * * * *` (1分) | 高流量服務，死亡容忍度低 |
| `*/5 * * * *` (5分) ✅ | 一般服務，平衡負擔與響應 |
| `*/10 * * * *` (10分) | 非關鍵服務，低開銷優先 |

## 驗證 Watchdog 運作中

```bash
cronjob action=list
# 檢查 last_status = "ok" 及 last_run_at
```

## 注意陷阱

- **勿用 `&` 在 foreground terminal 啟動伺服器** — 會被行程管理卡住。改用 `terminal(background=True)` 或腳本內直接 `&`
- **勿設為 agent-driven** — watchdog 無需 LLM 推理，`no_agent=true` 節省大量 token 並避免 LLM 延遲
- **啟動後 `sleep 2`** 再驗證 — 給伺服器初始化時間，避免 race condition
- **`sudo pkill -f` 要確認 pattern 夠獨特** — 以免誤殺其他進程
- **port 監聽檢查比純 pgrep 可靠** — 進程活著但 socket 已關閉的 zombie 狀態單靠 pgrep 抓不到
