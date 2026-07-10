---
name: backend-api-diagnostics
description: "假設驅動診斷法 — 對 FastAPI / 後端 API 服務進行路由層智慧診斷與修復"
status: stable
---

# Backend API Diagnostics

## 📖 Description

假設驅動診斷法 (Hypothesis-Driven Diagnosis) for FastAPI and backend API services. Follows a structured protocol: Recon → Hypothesis → Verify → Fix → Regression → Report, with strength routing to control reasoning depth at each step.

**When to load:** User reports a 404/500/503 on an API endpoint; a backend service is misbehaving; a route returns unexpected results; the user asks "why is this API broken".

---

## Core Protocol

### Strength Routing

| Level | When | API Setting | Behavior |
|:-----:|:-----|:-----------|:---------|
| **L1** 快速 | Recon / Health-check / Regression | `thinking: false` | Mechanical execution, direct output, no reasoning chain |
| **L2** 標準 | Single-root-cause fix / diff writing | `thinking: true` | Standard reasoning |
| **L3** 深度 | Hypothesis generation / cross-module fault / failed diagnosis | `reasoning_effort: high` | Full reasoning; exhaust hypothesis space |

**Rules:**
- Each step MUST declare its level before starting
- If L1 finds an anomaly → STOP, escalate to L2 before re-evaluating
- If the same root cause fails verification ≥2 times → forced L3 escalation
- L3 on mechanical steps = violation (token waste)

---

### 6-Step Diagnostic Flow

#### 1. Recon (L1)

```
Read: routing decorators, middleware, dependency injection
Output: actual registered route table (all methods + paths)
Do NOT make root-cause judgments at L1
```

**Commands:**
```bash
# Health check all known endpoints
curl -s --max-time 5 http://host:port/api/status
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://host:port/api/chat ...

# Read route registration code
grep -n "@app\.\(get\|post\|put\|delete\|patch\)" server.py
```

#### 2. Hypothesis Generation (L3)

List possible root causes sorted by probability, each with verification method.

**Template:**
```
| # | Hypothesis | Probability | Verification Method |
|---|------------|:----------:|--------------------|
| 1 | Route doesn't exist | 🔴 High | Read route decorator at line N |
| 2 | Middleware ordering issue | 🟡 Medium | Check middleware stack order |
| 3 | Schema mismatch | 🟡 Medium | curl with correct payload → still 404 = excluded |
| 4 | Running stale code | 🟢 Low | Compare /proc/PID with disk file |
```

#### 3. Verification (L2)

Verify each hypothesis with cheapest-cost method first (curl → unit test → log inspection).

**Do NOT modify code before verification step completes.**

#### 4. Fix (L2)

- **Backup before any edit**: `cp file.py file.py.bak.$(date +%s)`
- **Minimum diff**: ONLY touch the faulty area. Add alias routes, not duplicate logic.
- **Do NOT** change existing endpoint paths or response schema (frontend depends on them)
- If multiple root causes, fix ONE at a time

**Common fix patterns:**
```python
# Route alias (when frontend calls wrong path)
@app.post("/api/real-path")
async def existing_handler(req: Request): ...

@app.post("/api/expected-path")  # ALIAS — was 404
async def expected_alias(req: Request):
    return await existing_handler(req)
```

#### 5. Regression (L1)

Run ALL endpoints after fix, including the previously broken one:

```bash
# Test the fixed endpoint
curl ...  # expect 200, not 404

# Test ALL other endpoints (at minimum 5-8)
curl /api/status      # health
curl /api/chat/ask    # core functionality  
curl /api/chat/stream # long-running (90s+ timeout scenario)
curl /api/providers   # listing
curl /api/history     # data retrieval
```

**All must pass before reporting done.**

#### 6. Report (L1)

Markdown report containing:
- **Root cause** (one sentence)
- **Evidence** (the curl output or log line that proved it)
- **Fix diff** (the minimal change)
- **Verification results** (command + actual output for all 8+ endpoints)
- **Rollback command** (so the fix can be undone)
- **Strength usage statistics** (L1/L2/L3 per step)

---

## Constraints

- ❌ Never modify code without completing verification first
- ❌ Never fix more than one root cause at a time
- ❌ Never change existing endpoint paths or response schema
- ❌ Never guess — output "Cannot diagnose" + eliminated hypotheses list if root cause can't be found
- ✅ Always back up before editing
- ✅ Always include rollback command in report

## Pitfalls

- **Port conflicts:** When restarting a server, the old process may still hold the port. Kill it first: `sudo pkill -f server.py` before starting the new one. A background=true start on a busy port fails silently (no error output).
- **Stale .pyc cache:** If the file on disk is patched but the running server still shows old behavior, clear bytecode cache: `find <project> -name "*.pyc" -delete`
- **Process user mismatch:** The server may run as a different user than you expect. Check with `ps -o user,pid,comm`. DB file permissions depend on the process user.
- **Docker volume permissions:** A server running as `ysga1` cannot read files under `/var/lib/docker/volumes/` unless `docker/` and `volumes/` directories have `+rx` for world. Fix: `sudo chmod +rx /var/lib/docker/ /var/lib/docker/volumes/`
- **Secret redactor hides real values:** `«redacted:sk-…»` in `read_file` output is NOT the actual key. Always use `len()` in Python to verify real length before using the value in code.
