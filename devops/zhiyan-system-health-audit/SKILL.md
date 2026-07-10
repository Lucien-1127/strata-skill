---
name: zhiyan-system-health-audit
description: Audit the Zhiyan AI memory and storage stack health.
version: 0.2.0
author: Hermes
platforms: [linux]
tags:
  - Zhiyan
  - Diagnostics
  - Audit
  - Memory
  - RAG
---

# Zhiyan System Health Audit

Periodic health audit of the entire Zhiyan AI infrastructure **memory/storage stack** in one structured pass: Mem0 (long-term memory), Qdrant vector store, ChromaDB RAG index, STRATA compression pipeline, state.db session tracking, and skills/docs file management. Produces an actionable health report with optimization recommendations.

Does **not** cover Hermes Agent internal state (skills split, curator, hub sync) — use `hermes-system-diagnostics` for that. Does **not** cover VM-level infrastructure (disk, swap, uptime) — use `managing-hermes-legal-system` for that.

## When to Use

- Boss asks "狀況如何" / "長期記憶狀況" / "系統健康檢查"
- Before deploying a system update to ensure all storage layers are healthy
- After installing or reconfiguring Mem0, Qdrant, or ChromaDB
- Weekly or bi-weekly maintenance routine
- When RAG search returns stale or missing results

## Prerequisites

- Access to `~/.hermes/` directory
- Qdrant running on `localhost:6333`
- zhiyan-search project at `/home/ysga1/zhiyan-search/`
- zhiyan-legal repo at `/home/ysga1/zhiyan-legal/`
- Hermes `mem0_list` tool available (session-context)
- Python3 with chromadb installed

## Procedure

Run all checks in parallel where possible (they are independent). Then synthesize findings.

### 1. Mem0 Long-Term Memory

Use the `mem0_list` tool to retrieve all stored memories. Evaluate:
- **Count**: How many memories? Fewer than 30 suggests the system is not capturing enough context.
- **Quality**: Are memories substantive (preferences, project facts, corrections) or trivial?
- **Freshness**: Check timestamps — is recent session content missing?

```bash
# Mem0 list via tool (cannot be run from terminal — use the mem0_list tool directly)
```

### 2. Qdrant Vector Store Health

Verify Qdrant is online and the `mem0` collection exists:

```bash
curl -s http://localhost:6333/collections
```

Expected: response contains `{"name":"mem0"}` and `{"name":"mem0migrations"}`.

### 3. ChromaDB / zhiyan-search RAG Index

Check vector store integrity and details:

```bash
cd /home/ysga1/zhiyan-search

# File-level health
ls -la vector_store/chroma.sqlite3  # should exist, ~11MB typical

# Python health check
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='./vector_store/')
col = c.get_collection('zhiyan_docs')
print(f'Chunks: {col.count()}')
samples = col.get(limit=3)
for i, (id, meta) in enumerate(zip(samples['ids'], samples['metadatas'])):
    print(f'  [{i}] {meta.get(\"source\",\"?\")[:50]}')
"
```

Expected: chunk count > 0 (1,700+ typical), metadata has source paths.

### 4. STRATA Compression Pipeline

Verify the auto-compression cronjob is healthy:

```bash
hermes cron list
```

Check for:
- STRATA自動壓縮 job is `[active]`
- `Last run:` is recent (within the last 2-3 hours)
- Next run is scheduled

Check compression lock state for deadlocks:

```bash
python3 -c "
import sqlite3, os, time
db = os.path.expanduser('~/.hermes/state.db')
conn = sqlite3.connect(db)
c = conn.cursor()
rows = c.execute('SELECT * FROM compression_locks ORDER BY rowid DESC LIMIT 5').fetchall()
for r in rows:
    session_id = r[0]
    lock_type = r[1]
    expires = r[3]
    remaining = int(expires - time.time())
    status = '🟢 ACTIVE' if remaining > 0 else '🔴 EXPIRED'
    print(f'{status} | {lock_type} | {session_id[:30]}... | expires in {remaining}s' if remaining > 0 else f'{status} | {lock_type} | {session_id[:30]}...')
"
```

### 5. state.db Session Health

Check recent session activity and volume:

```bash
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/state.db')
conn = sqlite3.connect(db)
c = conn.cursor()
# Total session count
total = c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
print(f'Total sessions: {total}')
# Recent 10
rows = c.execute('SELECT started_at, id, title, message_count FROM sessions ORDER BY started_at DESC LIMIT 10').fetchall()
for r in rows:
    print(f'  {str(r[0])[:16]} | {r[1][:12]}... | msg:{r[3]} | {str(r[2])[:40]}')
"
```

### 6. Skills & Reference File Health

Audit how many skills have reference/template/script files:

```bash
echo '=== Skills Reference Coverage ==='
for skill in ~/.hermes/skills/*/; do
    name=$(basename "$skill")
    refs=$(find "$skill/references" -name '*.md' 2>/dev/null | wc -l)
    templates=$(find "$skill/templates" -name '*' 2>/dev/null | wc -l)
    scripts=$(find "$skill/scripts" -name '*' 2>/dev/null | wc -l)
    echo "  $name → refs:$refs templates:$templates scripts:$scripts"
done
```

### 7. FreeLLM API Token Usage Analytics

Check token consumption by model, daily usage patterns, and error rates through the FreeLLM API's internal SQLite database:

```bash
DB=/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db

# Top models by total tokens
sudo sqlite3 -column -header "$DB" "
SELECT model_id,
       COUNT(*) as calls,
       SUM(input_tokens) as total_input,
       SUM(output_tokens) as total_output,
       SUM(input_tokens + output_tokens) as total_tokens,
       ROUND(AVG(latency_ms)) as avg_latency_ms,
       ROUND(SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as error_pct
FROM requests
GROUP BY model_id
ORDER BY total_tokens DESC
LIMIT 15;
"

# Daily usage (last 7 days)
sudo sqlite3 -column -header "$DB" "
SELECT DATE(created_at) as day,
       COUNT(*) as calls,
       SUM(input_tokens + output_tokens) as total_tokens
FROM requests
WHERE created_at >= DATE('now', '-7 days')
GROUP BY day
ORDER BY day DESC;
"

# Overall totals
sudo sqlite3 "$DB" "SELECT COUNT(*) as total_calls, SUM(input_tokens + output_tokens) as total_tokens FROM requests;"
```

Key metrics to report:
- **Total token burn**: sum of all input+output tokens
- **Top models by consumption**: which models drive the most token cost
- **Daily pattern**: which days had highest usage (usually research days)
- **Error rates**: models with >30% error rate should be investigated or deprioritized

The FreeLLM API also exposes an admin analytics API (session-cookie auth, email field not username):
- `POST /api/auth/login` with `{email, password}` → session cookie
- `GET /api/analytics/summary` — overall stats (admin auth required)

### 8. zhiyan-legal Docs Structure

Quick directory layout audit:

```bash
ls -d /home/ysga1/zhiyan-legal/docs/*/ | while read d; do
    name=$(basename "$d")
    count=$(ls "$d"*.md 2>/dev/null | wc -l)
    echo "  $name → $count files"
done
```

### 9. Mini App Server & Key Registry

The Mini App (金鑰管理 dashboard) serves at port 8081 and `zhiyan.dev/m/`. It can die silently or serve stale content due to Cloudflare cache.
The API backend queries FreeLLM's SQLite DB at `/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db` for model lists — if the Docker volume path is not readable by `ysga1`, `/api/models` silently returns empty.

```bash
# 0. Docker volume accessible?
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('/var/lib/docker/volumes/zhiyan_freellmapi-data/_data/freeapi.db')
    count = conn.execute('SELECT COUNT(*) FROM models').fetchone()[0]
    print(f'🟢 Docker volume accessible: {count} models')
    conn.close()
except Exception as e:
    print(f'🔴 Docker volume BLOCKED: {e}')
    print('Fix: sudo chmod +rx /var/lib/docker/ /var/lib/docker/volumes/')
"

# 1. Process alive?
ps aux | grep miniapp-server | grep -v grep || echo "🔴 MINIAPP DOWN"

# 2. Port listening?
ss -tlnp | grep 8081 || echo "🔴 PORT 8081 NOT LISTENING"

# 3. API responsive?
curl -s --max-time 5 http://127.0.0.1:8081/api/keys | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"keys\"])} keys')" 2>/dev/null || echo "🔴 API UNREACHABLE"

# 4. Frontend serving correctly? (bypass CF cache)
ACTUAL=$(curl -s -H 'Host: zhiyan.dev' http://127.0.0.1/m/ | head -3)
echo "$ACTUAL" | grep -q "zh-TW" && echo "🟢 Frontend v3" || echo "🔴 Frontend stale/wrong"

# 5. Cloudflare tunnel alive?
ps aux | grep cloudflared | grep -v grep | head -1 || echo "🔴 NO TUNNEL"

# 6. Key registry integrity
python3 -c "
import json, os
r = os.path.expanduser('~/.hermes/env/keys-registry.json')
d = json.load(open(r))
print(f'Registry: {len(d)} keys, platforms: {len(set(k[\"platform\"] for k in d))}')
for k in d:
    env_file = k.get('env_file', 'N/A')
    exists = os.path.exists(os.path.join(os.path.expanduser('~/.hermes/env/'), env_file)) if env_file != 'N/A' else True
    tested = '✅' if k.get('valid') else ('❌' if k.get('tested') else '⬜')
    print(f'  {tested} {k[\"platform\"]:12s} {k[\"label\"][:25]:25s} env={\"✔️\" if exists else \"✖️\"}')
"
```

## Health Report Synthesis

After all checks complete, produce a structured report:

| System | Status | Key Metric | Anomaly Flag |
|--------|--------|-----------|--------------|
| Mem0   | 🟢/🟡/🔴 | N memories | Stale / Missing / Fine |
| Qdrant | 🟢/🔴 | Collections | Online / Offline |
| ChromaDB | 🟢/🟡/🔴 | N chunks | Stale / Missing / Fine |
| STRATA | 🟢/🔴 | Last run time | Dead / Healthy |
| state.db | 🟢 | N sessions | Growth rate |
| **FreeLLM API** | 🟢/🟡 | Token spend / error % | Top model >40% errors? Unusual daily spike? |
| Skills refs | 🟢/🟡 | Rich skills / N | Coverage gaps |
| Mini App | 🟢/🔴 | PID + keys | Server dead / Stale frontend / CF cache |
| Docs | 🟢 | N dirs | Structural issues |

## Optimization Recommendations

Flag these common gaps when found:

| Finding | Recommendation |
|---------|---------------|
| Mem0 < 30 memories | STRATA compression should dual-write summaries to Mem0 (not just MEMORY.md) |
| ChromaDB last build is old | Add a cronjob to auto-rebuild when docs/ changes |
| Most skills have 0 refs | Consolidate narrow skills into class-level umbrellas with rich references/ |
| Compression locks expired/deadlocked | Clear stale locks manually from `compression_locks` table |

## Pitfalls

- **TOML vs YAML in config**: zhiyan-search uses YAML (`config.yaml`). Don't confuse with Hermes TOML config.
- **ChromaDB readonly database**: Rust bindings in ChromaDB 1.5.9 may lock on multi-batch `collection.add()`. Always batch all chunks into one `add()` call.
- **Qdrant Docker vs local**: Qdrant must run as Docker Server HTTP mode (`:6333`), not local mode, to avoid file locking.
- **state.db schema varies**: Column names differ across Hermes versions — use `PRAGMA table_info(sessions)` to discover columns before querying.
- **mem0_list not available in terminal**: Must be called as a tool from an active Hermes session, not from a shell script.

## Verification

The simplest "all clear" check:

```bash
python3 -c "
import chromadb, os, sqlite3, json

# 1. ChromaDB
c = chromadb.PersistentClient(path='/home/ysga1/zhiyan-search/vector_store/')
chunks = c.get_collection('zhiyan_docs').count()
print(f'ChromaDB: {chunks} chunks ✅')

# 2. Mem0 dir
mem_count = len(os.listdir(os.path.expanduser('~/.hermes/env/')) | 0)
print(f'Mem0 env dir: accessible')

# 3. state.db sessions
db = os.path.expanduser('~/.hermes/state.db')
conn = sqlite3.connect(db)
total = conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
print(f'Sessions: {total} total ✅')
conn.close()

# 4. Skills total
skills = [d for d in os.listdir(os.path.expanduser('~/.hermes/skills/')) if os.path.isdir(os.path.join(os.path.expanduser('~/.hermes/skills/'), d))]
print(f'Skills: {len(skills)} total')
"
```
