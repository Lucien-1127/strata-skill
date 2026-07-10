---
name: hermes-system-diagnostics
description: Diagnose and recover Hermes Agent system state issues.
version: 0.1.0
author: Hermes
platforms:
- linux
metadata.hermes.tags:
- Hermes
- Diagnostics
- Recovery
- Troubleshooting
---

# Hermes System Diagnostics
Diagnose Hermes Agent internal state issues — missing skills, broken curator, hub sync failures, stale config — and recover to a working state. Does NOT cover provider/model connectivity (use `hermes doctor` for that).

## When to Use
- Skills list shows far fewer skills than expected
- Curator runs report zero agent-created skills despite known skill creation
- `skills-all/` directory exists but `skills/` is sparse or empty
- After profile migration or config change that may have split skill directories
- `.usage.json` doesn't track known skills

## Common Diagnostic Patterns
- **Skills split**: skills/ vs skills-all/ divergence → see references/skills-split-case-study.md
- **API key not found by Gateway**: key is set in shell env but missing from ~/.hermes/.env → see references/gateway-api-key-mismatch.md
- **Concurrent Hermes subagent modifying files**: Another Hermes session silently overwrites file writes. Diagnosis: ps aux | grep for hermes-snap processes. Recovery: kill the conflicting PID.
- **Mem0 429 All models exhausted**: Logs show LLM extraction failed with 429. Root cause: mem0.json oss.llm.config.openai_base_url points to FreeLLM (localhost:3001/v1). Fix: change to DeepSeek direct (https://api.deepseek.com/v1). Embedder can keep using FreeLLM. See local-embedder-mem0-setup skill.
- **Cron job "provider authentication error"**: A cron job fails with `provider authentication error` but interactive sessions work fine. Root cause: the gateway was restarted and the provider's API key env var was missing from the cron execution context. Diagnosis workflow below.
- **API / Mini App endpoint returns empty data**: Backend returns `[]` or `{}` for data that should exist. Root cause: the service process cannot read its SQLite database due to directory permissions (`/var/lib/docker/` not traversable by non-root). Diagnostics: `python3 -c "import sqlite3; conn = sqlite3.connect('/var/lib/docker/volumes/.../data.db')"`. Fix: `sudo chmod +rx /var/lib/docker/` and intermediate directories.

## Prerequisites
- Hermes Agent installed
- Access to `~/.hermes/` directory

## How to Run
Use `terminal` to inspect key directories and files, then `skill_view` and `skills_list` to verify recovery.

## Quick Reference
- `skills-all/` vs `skills/` — compare with `comm -23 <(ls skills-all/ | sort) <(ls skills/ | sort)`
- `.usage.json` — tracks active skill states
- `.curator_state` — curator run history and configuration
- `logs/curator/` — detailed curator run reports
- `.hub/taps.json` — hub sync state
- `hermes curator status` — curator health
- `hermes skills list` — active skill inventory
- `hermes doctor` — general system health

## Procedure

### Step 1: Compare skill inventories
Check if `skills-all/` has skills missing from `skills/`:
```bash
comm -23 <(ls ~/.hermes/skills-all/ | sort) <(ls ~/.hermes/skills/ | sort)
```
If the output lists many skills and `skills-all/` was created earlier than `skills/`, the directories are split.

### Step 2: Verify skills-all content integrity
Spot-check several SKILL.md files for valid frontmatter and content:
```bash
for dir in ~/.hermes/skills-all/name1 ~/.hermes/skills-all/name2; do
    head -6 "$dir/SKILL.md"
done
```

### Step 3: Check curator state
```bash
cat ~/.hermes/skills/.curator_state
hermes curator status
```
If curator reports 0 agent-created skills but `skills-all/` has many, the curator is looking at the wrong directory or hasn't been seeded.

### Step 4: Check hub sync state
```bash
cat ~/.hermes/skills-all/.hub/taps.json
cat ~/.hermes/skills/.hub/lock.json
```
If `taps` is empty but `skills-all/` has skills, the hub sync metadata may be stale.

### Step 5: Check timestamps
```bash
stat -c '%y %n' ~/.hermes/skills ~/.hermes/skills-all
```
If `skills/` was created significantly later than `skills-all/`, a migration or reset likely occurred.

### Step 6: Inspect curator run reports
```bash
ls -la ~/.hermes/logs/curator/
read_file ~/.hermes/logs/curator/<latest>/REPORT.md
read_file ~/.hermes/logs/curator/<latest>/run.json
```
`run.json` shows `counts.before` and `counts.after` — if both are 0, curator saw nothing.

### Step 7: Check config for skill paths
```bash
grep -i "skill" ~/.hermes/config.yaml
```
Absence of `skills.path` means the default `skills/` directory is used.

### Step 8: Recovery
If `skills-all/` is intact and `skills/` is sparse, copy skills back:
```bash
# Dry-run: list what would be copied
comm -23 <(ls ~/.hermes/skills-all/ | sort) <(ls ~/.hermes/skills/ | sort) > /tmp/missing-skills.txt
# Copy each missing skill
while read name; do
    cp -r ~/.hermes/skills-all/"$name" ~/.hermes/skills/"$name"
done < /tmp/missing-skills.txt
```
Then verify: `hermes skills list` should show the restored skills.

### 殘留程序清理（Telegram polling conflict / port 佔用）

**症狀：**
- Log 出現 `Telegram polling conflict (1/5) — previous session still held open on Telegram's servers`
- `ss -tlnp | grep <port>` 顯示舊 PID，重啟後新程序無法 bind

**根因：**
1. Telegram 伺服器會保留舊的 `getUpdates` 連線約 30-60 秒
2. `sudo pkill -f` 殺掉舊程序後，若新程序立刻啟動但舊 socket 尚未釋放，會衝突
3. 舊程序掛掉但 socket 處於 `TIME_WAIT` 狀態

**修復程序：**
```bash
# 1. 確認誰佔用 port
ss -tlnp | grep 8001

# 2. 強制殺光所有相關程序
sudo pkill -f "server.py" || true
sleep 3  # 等待 socket 釋放

# 3. 確認 port 已釋放
ss -tlnp | grep 8001 || echo "port free"

# 4. 啟動新程序
python3 /opt/zhiyan-backend/server.py &  # 或用 terminal(background=true)

# 5. 若仍有 Telegram conflict — 這是 Telegram 伺服器端殘留，約 30-60 秒自動恢復
# Gateway 內建 5 次重試機制會處理，不需手動介入
```

**注意事項：**
- `systemctl --user restart hermes-gateway` 無法從 gateway 自身行程內執行（會 SIGTERM 自己）
- 需要從外部 shell 執行，或背景啟動
- 不要用 `nohup ... &` — 用 `terminal(background=true)` 讓 Hermes 管理生命週期

### 模型名稱棄用遷移

**情境：** 上游 API 宣布舊模型名將於某日期停用（如 DeepSeek `deepseek-chat` → `deepseek-v4-flash`）。

**修復原則：**
1. 只改「會被觸發」的配置 — cron job、gateway、活躍服務會用到的路徑
2. 已停用的服務（無 cron、無調用）可以不改
3. 改完後清除 .pyc cache：`find <project> -name "*.pyc" -delete`
4. 確認舊程序已死透：`sudo pkill -f "server.py"` + `ss -tlnp | grep <port>` 確認 port 已釋放
5. 新程序啟動後驗證：`curl <status_endpoint>` 確認 model name 已更新
6. 如果改完後 `curl` 仍顯示舊名 → 舊程序還佔著 port，沒 kill 成功

### Cron Job Provider Auth 診斷流程

**觸發條件：** Cron job 回報 `provider authentication error` 或 `no API key was found`。

**診斷步驟（按順序）：**

```bash
# 1. 找 gateway log 中的錯誤時間線
grep -n 'RuntimeError.*no API key\|provider auth' ~/.hermes/logs/gateway.log | tail -20

# 2. 確認 cron job 是否仍在排程中
hermes cron list  # 或 cronjob action='list'

# 3. 檢查 cron 輸出目錄是否有殘留
ls ~/.hermes/cron/output/<job_id>/ 2>/dev/null

# 4. 比對 config.yaml 是否有明文 key（Boss 規定禁止）
grep 'api_key' ~/.hermes/config.yaml
# 應為 api_key: _FROM_ENV_ 而非 api_key: sk-...

# 5. 檢查 systemd service 是否有 EnvironmentFile
grep 'EnvironmentFile' ~/.config/systemd/user/hermes-gateway.service
# 應包含 provider 的 env file 路徑

# 6. 檢查 shell rc 是否有明文 key
grep -n 'export.*API_KEY' ~/.profile ~/.bashrc ~/.zshrc
# 明文 key 必須替換為 source env file
```

**常見根因與修復：**

| 根因 | 修復 |
|:-----|:-----|
| `config.yaml` 有明文 `api_key: sk-...` | `hermes config set providers.<name>.api_key '_FROM_ENV_'` |
| systemd service 無 `EnvironmentFile` | 加入 `EnvironmentFile=/home/ysga1/.hermes/env/<provider>-<label>.env` |
| `~/.profile` 有 `export API_KEY=sk-...` | 改為 `set -a; . ~/.hermes/env/<env-file>; set +a` |
| gateway 重啟後 env var 遺失 | 以上三項修復後重啟 gateway 即可 |
| cron job 本身已不在排程中 | 不需修復 — job 已被移除，僅殘留錯誤通知 |

**注意：** 無法從 gateway 內部執行 `systemctl --user restart`（SIGTERM 會殺死自己）。需從外部 SSH 執行，或用 `terminal(background=true)` + `sleep 2` 繞過。systemd 變更儲存後須手動 `daemon-reload && restart`。

### 金鑰安全三層防護（Boss 規定）

## Pitfalls
- Curator only manages **agent-created** skills — bundled and hub-installed skills won't appear in its counts
- `.usage.json` per-directory tracks only skills in that directory
- `hermes skills list` reads from the active `skills/` directory, not `skills-all/`
- Curator dry-run mode (`--dry-run`) reports previews without applying changes
- Skill directories can diverge after profile-specific config changes or curator pruning
- **Gateway does NOT inherit shell env vars.** A provider API key set in `~/.bashrc` or `~/.profile` is only available to interactive shells, not to the Gateway daemon. Always add provider credentials to `~/.hermes/.env` instead, then restart the Gateway. If `hermes doctor` passes but the gateway errors with "no API key found", this is the likely cause.
- **HTTPS 000 response when HTTP 200 works.** If `curl -sk https://domain` returns 000 but `curl http://domain` returns 200, the firewall is blocking port 443. Check `sudo ufw status` and add `sudo ufw allow 443/tcp` then `sudo ufw reload`.
- **Nginx config change not taking effect.** If `nginx -t` passes and `nginx -s reload` succeeds but the old behavior persists, the previous nginx master process may still hold the old config. Kill it with `sudo pkill nginx && sudo nginx`. Also verify the correct config file was edited (`sites-available/` vs `sites-enabled/`).
- **Cannot restart gateway from inside the gateway.** `systemctl --user restart hermes-gateway` will SIGTERM the current process and kill your command before it completes. Use `terminal(background=true, notify_on_complete=true)` with `sleep 2 && systemctl ...` to execute from a detached process. Even `hermes gateway restart` is blocked. For systemd config changes: save the file, tell the user to restart, or schedule it via an external mechanism.

## Verification
After recovery, run:
```bash
hermes skills list
skill_view(name='<one of the recovered skills>')
```
Both should show the restored skills as available and readable.
