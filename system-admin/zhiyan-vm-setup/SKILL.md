---
name: zhiyan-vm-setup
description: A skill for configuring and maintaining the Zhiyan AI Legal System on a Google Cloud VM (Ubuntu 24.04). Covers system resource checks, swap setup, citation format updates, task router modifications, and service health verification.
status: stable
---
# Zhiyan VM Setup Skill

This skill provides a reusable procedure for configuring and maintaining the Zhiyan AI Legal System running on a Google Cloud VM (Ubuntu 24.04). It covers common administrative tasks such as verifying system resources, enabling swap, fixing citation formats, updating task routing rules, and ensuring service health.

## Prerequisites
- Access to the VM via SSH (using the appropriate key or gcloud compute ssh).
- sudo privileges on the VM.
- The FreeLLMAPI and zhiyan-legal services should be installed and running (or at least their configuration files present).

## Procedure

### 1. Verify System Resources
Check CPU, memory, disk usage, and running services to understand current state.

```bash
# CPU load and uptime
uptime

# Memory usage
free -h

# Disk usage for root and /mnt/data
df -h / /mnt/data

# Listening services
ss -tlnp | grep -E ':3001|:8000|:80|:22'

# Check key service processes
ps aux | grep -E 'hermes|freellm|python3.*server\.py|python3.*zhiyan' | grep -v grep
```

### 2. Ensure Swap is Configured (if needed)
If the VM lacks swap and you want a safety net, create a swap file on the attached data disk.

```bash
# Assuming a 10GB data disk is mounted at /mnt/data
sudo fallocate -l 2G /mnt/data/swapfile
sudo chmod 600 /mnt/data/swapfile
sudo mkswap /mnt/data/swapfile
sudo swapon /mnt/data/swapfile
# Make it permanent
echo '/mnt/data/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
# Verify
swapon --show
free -h
```

### 3. Fix Citation Format (if using outdated style)
Update the citation policy to use the new inline superscript format (e.g., `^[來源簡稱]`) and ensure all relevant files reflect this.

#### Edit SPACE_CORE v3.02
File: `docs/10_核心控制層/13_空間核心規格_PPL_SPACE_CORE_v3.0.0.md`
- Set G3 to: `|| **G3. 引用格式** | 正文句尾用：^[來源簡稱]（例：^[民法§184]、^[判決字號]、^[契約書.pdf]） |`
- Ensure version is bumped (e.g., v3.02_HYBRID).

#### Edit CITATION_POLICY v2.3.0
File: `docs/20_模式與引用層/30_引用政策_CITATION_POLICY_v2.0.0.md`
- Update version to v2.3.0.
- Change all instances of `[1][2]…` to `^[來源簡稱]` in sections C2.1, C2.2, C4.1, C4.2, C4.3, and version table.
- Keep C5.4 (source credibility mapping) unchanged.

#### Remove legacy `[1][2]` markers
Run a project‑wide replacement (backup first):
```bash
find /home/ysga1/zhiyan-legal -type f \( -name "*.md" -o -name "*.txt" \) -exec sed -i 's/\[\d\+\]//g' {} +
```
Then re‑apply the new format where needed (the policy files already contain the correct format).

### 4. Update Task Router (TASK_ROUTER v1.1.0)
Add missing mappings and arbitration rules.

File: `docs/10_核心控制層/15_任務路由表_TASK_ROUTER_v1.0.0.md`

- In the **快速路由表** add:
  ```
  || 契約審查、合約風險、合約條款、違約責任 | CONTRACT_RISK | `49_模組_合約風險策略_CONTRACT_RISK_v1.0.0.md` ||
  || 法律書狀、起草書狀、民事起訴狀、刑事上訴書、答辯狀 | LEGAL_WRITER | `48_人格_法律書狀師_LEGAL_WRITER_v1.0.0.md` ||
  ```
- In the **衝突處理** section add:
  ```
  || R-申論仲裁 | 若同時觸發 TA_REVIEW 與 ESSAY_TEST → 偵測到「批改」「評分」「幾分」「哪裡錯」→ 導向 TA_REVIEW；偵測到「出題」「考我」「練習」「測試」→ 導向 ESSAY_TEST；兩者皆無 → 追問：「您是要批改一份答案，還是想讓我出題考您？」 ||
  || R-開庭仲裁 | 若同時觸發 LITIGATION 與 COURTROOM → 偵測到「模擬」「演練」「角色扮演」「扮演法官/律師」→ 導向 COURTROOM；否則一律導向 LITIGATION（真實訴訟優先原則） ||
  ```
- Bump version to v1.1.0.

### 5. Verify Service Health
After making changes, ensure the services are still running.

```bash
# Check FreeLLMAPI
curl -s http://127.0.0.1:3001/ | head -5

# Check zhiyan-legal API (if running on port 8001)
curl -s http://127.0.0.1:8001/ | head -5

# Check Nginx admin proxy
curl -I -u lucien127@proton.me:Lucien.489 http://zhiyan.dev/admin/ | head -2

# Optional: run the Zhiyan test suite to confirm nothing broke
cd /home/ysga1/zhiyan-legal && python3 -m pytest tests/ -x --tb=short
```

## Notes
- Always back up configuration files before editing (e.g., `cp file file.bak`).
- After editing nginx config, test with `sudo nginx -t` before reloading.
- If you encounter auth errors when updating the .htpasswd file, ensure you use `htpasswd -bc` to create a new file or `-b` to modify an existing one.
- The swap file is placed on the attached 10GB data disk (`/mnt/data`) to preserve the root disk for system use.
- **Port contention during restart**: When restarting a Python FastAPI service, the old process may still hold the port. The new process will silently fail (no error message) without producing any output. **Fix**: `sudo pkill -f server.py && sleep 2 && ss -tlnp | grep <port>` to verify the port is free before starting the new process. A background process started before the old one dies will never bind.
- **`.pyc` cache staleness**: Python caches compiled bytecode in `__pycache__/` and `*.pyc` files. If source code is edited (e.g., changing a default config value), the old `.pyc` may be loaded instead of the new source. **Fix**: `find <project_dir> -name "*.pyc" -delete` before restarting.
- **Stale config as time bomb**: A config entry pointing to a deprecated model name, expired API key, or unused endpoint is not harmless — if any code path ever hits it (cron job, auto-restart, fallback routing), it will fail silently or loudly at the worst moment. **Principle**: fix deprecated configs proactively even if you think nothing currently uses them.

## References
- `references/swap-creation.md` – detailed steps and validation for adding swap.
- `references/citation-format-change.md` – diff of the citation policy changes.
- `references/task-router-update.md` – excerpt of the updated task router sections.