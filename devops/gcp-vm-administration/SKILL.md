---
name: gcp-vm-administration
description: Administer and verify GCP VM state from within the VM itself. Covers the 'SSH trap', service health checks, disk verification, and SSH/GIT configuration.
status: stable
---

# GCP VM Administration

Use this skill whenever you need to check the health of a GCP VM, verify services are running, confirm disk mounts, or debug SSH/Git issues — **while running on the VM itself**.

## ⚠️ Pitfall #1: The "SSH Into Yourself" Trap

**If you are running on a GCP VM, you ARE on the machine. Do NOT attempt to SSH into it.**

### How to detect if you are already on the target VM

```bash
# Check if this is a GCP VM hostname
hostname -f | grep -E "\.(c\.|googleusercontent\.com)" && echo "This IS a GCP VM"

# Or check for GCE metadata service (only works on GCE instances)
curl -s --max-time 2 -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/name 2>/dev/null
```

### Symptoms of this mistake
- Running `ssh <user>@<external-ip>` from the VM itself
- Trying to use `gcloud compute ssh` when already inside the target VM
- The user says something like "VM 就是本機" (the VM _is_ the local machine)

### Correct approach
- Skip SSH entirely
- Run commands directly (you are already on the machine)
- If you need `gcloud` commands, they work locally (for metadata about the VM, project, etc.)

## 🔍 Service Health Verification

### Check all critical services at once

```bash
echo "=== FreeLLMAPI ===" && curl -s http://localhost:3001 | head -1
echo "=== zhiyan-legal ===" && curl -s http://localhost:8000 | head -1
echo "=== Hermes Gateway ===" && ps aux | grep hermes | grep -v grep
echo "=== GitHub SSH ===" && ssh -T git@github.com 2>&1 | head -1
```

### Individual service checks

| Service | Port | Quick Check |
|---------|------|-------------|
| FreeLLMAPI | :3001 | `curl -s http://localhost:3001` |
| zhiyan-legal | :8000 | `curl -s http://localhost:8000` |
| Hermes Gateway | — | `ps aux \| grep hermes` |

### Check a specific Python process is running

```bash
ps aux | grep "hermes_cli.main gateway run" | grep -v grep
```

## 💾 Disk and Mount Verification

### Verify a disk is mounted

```bash
lsblk --filter="MOUNTPOINT!=\"\""  # show only mounted
```

### Check specific mount point usage

```bash
df -h /mnt/data
```

### Verify /etc/fstab has persistent mount

```bash
grep /mnt/data /etc/fstab
# Expected: UUID=<uuid> /mnt/data ext4 defaults 0 2
```

### Quick mount status check

```bash
findmnt /mnt/data
```

## 🔑 SSH / Git Configuration Verification

### Test GitHub SSH connection

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

### Check git remote URL

```bash
cd /path/to/repo && git remote -v
# Should show: git@github.com:<user>/<repo>.git (SSH, not HTTPS)
```

### Check SSH key exists and is registered

```bash
cat ~/.ssh/id_ed25519.pub  # or id_rsa.pub, etc.
```

## 🎛️ System Information Gathering

### Quick system overview

```bash
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Uptime: $(uptime -p)"
```

### Check memory

```bash
free -h
```

### Check disk usage

```bash
df -h
```

### List running processes matching a pattern

```bash
ps aux | grep "<pattern>" | grep -v grep
```

## 📋 Full Health Check Script: run when user says "check system" or "verify services"

Run this complete check and present results in a table:

```bash
echo "=== 系統基本資訊 ===" && hostname && date
echo "=== 磁碟掛載狀態 ===" && lsblk | grep -E "NAME|sdb"
echo "=== /mnt/data ===" && df -h /mnt/data 2>/dev/null
echo "=== fstab ===" && grep /mnt/data /etc/fstab
echo "=== FreeLLMAPI ===" && curl -s http://localhost:3001 | head -1
echo "=== zhiyan-legal ===" && curl -s http://localhost:8000 | head -1
echo "=== Hermes ===" && ps aux | grep hermes | grep -v grep | head -1
echo "=== GitHub SSH ===" && ssh -T git@github.com 2>&1 | head -1
cd /home/ysga1/zhiyan-legal 2>/dev/null && echo "=== Git Remote ===" && git remote -v
echo "=== Memory ===" && free -h | head -2
echo "=== Disk Usage ===" && df -h | head -5
```

### External Connectivity & DNS Check

When a domain-based service is unreachable from outside, the problem may be DNS, not the server. Run this alongside the full health check:

```bash
# 1. VM's public IP
MY_IP=$(curl -s ifconfig.me)
echo "VM public IP: $MY_IP"

# 2. DNS resolution per domain — detect DNS → wrong IP
for domain in zhiyan.dev lucien126.com www.lucien126.com; do
    IP=$(dig +short $domain A 2>/dev/null | head -1)
    if [ -z "$IP" ]; then
        echo "$domain → (no A record)"
    elif [ "$IP" = "$MY_IP" ]; then
        echo "$domain → $IP ✅ matches VM"
    else
        echo "$domain → $IP ❌ MISMATCH (VM is $MY_IP)"
    fi
done

# 3. Check DNS registrar
echo "=== NS records ==="
dig +short NS zhiyan.dev 2>/dev/null | head -3
dig +short NS lucien126.com 2>/dev/null | head -3

# 4. Test external accessibility via nginx
for endpoint in http://localhost:80 https://localhost:443; do
    status=$(curl -sk -o /dev/null -w "%{http_code}" $endpoint 2>/dev/null)
    echo "$endpoint → $status"
done
```

### Firewall & Port Inventory

```bash
echo "=== Listening ports (key services) ==="
ss -tlnp | grep -E ':(80|443|300[01]|800[01]|808[12]|10274)'

echo "=== iptables policy (INPUT chain) ==="
sudo iptables -L INPUT -n 2>/dev/null | head -10
echo "=== nftables (port 443) ==="
sudo nft list ruleset 2>/dev/null | grep -E 'dport 443|dport 80' | head -5 || echo "(not using nftables)"
```

### Service-Level HTTP Verification

Check each service responds with the expected status code on its actual endpoint:

```bash
echo "=== Service health by HTTP status ==="
for check in "8001|zhiyan.dev (backend)" "3001|FreeLLM API" "8082|API backend" "8081|Mini App"; do
    port=$(echo $check | cut -d'|' -f1)
    label=$(echo $check | cut -d'|' -f2)
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/ 2>/dev/null)
    echo "  :$port $label → $status"
done
```

## 📋 Project-Level Verification After Setup

After confirming all services are running, verify the project code itself landed correctly:

### Quick project health check
```bash
cd /home/ysga1/zhiyan-legal
git status                    # clean? any untracked files?
git log --oneline -3         # recent commits
python3 -m pytest tests/ -q  # test suite — expect all green
```

### Common post-setup pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Version reference mismatch** | Test fails looking for `file_v1.1.0.md` but actual file is `file_v1.2.0.md` | Update manifest.py to reference the current filename |
| **Untracked data artifacts** | `git status` shows `data/*.db` files | Add to `.gitignore` before first commit |
| **Missing test deps** | `pytest: command not found` or ModuleNotFoundError | `pip install pytest pytest-cov` |
| **Wrong git remote** | `git push` fails with auth error | Check `git remote -v` uses `git@github.com:` not `https://` |

### Trace-and-fix workflow for test failures

1. Run the full suite: `python3 -m pytest tests/ -v`
2. Read the **failure message** carefully — it tells you which file path is expected vs actual
3. Search the manifest/source for the expected path:
   ```bash
   grep -rn "old_filename" src/ tests/
   ```
4. Check the actual file exists on disk with current version:
   ```bash
   ls docs/path/to/directory/
   ```
5. Update the manifest to match the actual filename (one-line patch)
6. Re-run tests to confirm fix

Real-world example: `tests/test_manifest.py` expected `51_人格_助教批改_v1.1.0.md` but the actual file had been bumped to `v1.2.0.md`. Fix: update the filename in `manifest.py`.

See `references/post-setup-project-verify-2026-07-04.md` for the full session transcript of this pattern.

## ⚡ When User Sees "本地" (local) vs "VM"

**Rule of thumb**: If the user is running a Hermes session on a GCP VM, that VM IS the "local" environment for that session. Do not assume "local" means the user's laptop / desktop.

If the user says:
- "check 本地" or "check local" → run commands directly, no SSH
- "SSH to VM" or "connect to the machine" → verify if this is needed; you may already be there
- "VM is local" → understood; skip SSH, run everything directly

## 🗂️ Organization Tips

### Pitfall: Docker Volume Not Readable by Non-Root User

When a non-root user (e.g. `ysga1`) needs to read a Docker container's SQLite database (e.g. FreeLLM's `/var/lib/docker/volumes/*/_data/freeapi.db`), the restrictive Docker directory permissions (`drwx--x--- root root`) block traversal.

**Symptoms:** Mini App `/api/models` returns empty; `sqlite3.connect()` fails with `unable to open database file`; `namei -l` shows `Permission denied` at the `docker/` level.

**Fix:**
```bash
sudo chmod +rx /var/lib/docker/
sudo chmod +rx /var/lib/docker/volumes/
sudo chmod +rx /var/lib/docker/volumes/<volume-name>/
sudo chmod 644 /var/lib/docker/volumes/<volume-name>/_data/<db-file>
```
One-time fix — survives reboots.

### Pitfall: Server Port Contention After Config Change

**Symptom:** Modified `server.py` and restarted, but change doesn't take effect (old model name still showing, old routes still active).

**Root cause:** Old process still holds the port; new process silently fails to bind; the old process continues serving with stale config.

**Diagnosis & fix:**
```bash
# Who's on the port?
ss -tlnp | grep <PORT>

# Did the process restart?
ps -o pid,lstart,args -p <PID>
ls -la server.py  # compare modify time vs process start time

# Force nuke all instances
sudo pkill -f "server.py"
sleep 2
# Start fresh
nohup python3 server.py &

# Verify new config
curl -s http://localhost:<PORT>/api/status | python3 -c "import json,sys; print(json.load(sys.stdin)['model'])"
```

- Store all service configuration in `/home/ysga1/` (or equivalent project root)

- Store all service configuration in `/home/ysga1/` (or equivalent project root)
- Use `/mnt/data` for large files, logs, or data that should survive reboot
- Ensure all mount points are in `/etc/fstab` for persistence
- Keep SSH keys in `~/.ssh/` with correct permissions (`chmod 600` for private keys)
