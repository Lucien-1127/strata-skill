---
name: fastapi-diagnosis
description: "Systematic FastAPI route diagnosis with thinking-strength routing — locate the fault, minimal fix, full regression."
version: 0.1.0
author: Hermes Agent
tags: [fastapi, diagnosis, routing, backend]
---

# FastAPI Route Diagnosis

**假設驅動診斷法** — 先驗證、後修改。專精 FastAPI 路由層診斷與修復。

## When to Load

- User reports 404 / 502 / 500 on known API endpoints
- User asks "check why X endpoint is broken"
- Adding new API routes or fixing routing mismatches
- Any backend service health issue where the code needs inspection

## Core Protocol

### 1. Reconnaissance [L1 — fast, no reasoning chain]

Read the FastAPI route definitions, middleware stack, and dependency injection:

```bash
# Find the server entry point
ls /opt/zhiyan-backend/server.py
grep -n "@app\.\(get\|post\|put\|delete\|patch\)" server.py

# Check middleware
grep -n "add_middleware\|CORSMiddleware" server.py

# Check static file mounts (can shadow routes)
grep -n "StaticFiles\|mount\|NoCacheStaticFiles" server.py
```

Also run a health check on known endpoints:
```bash
for ep in /api/status /api/chat /api/committee/run; do
    echo -n "$ep → "
    curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8001$ep 2>/dev/null || echo "UNREACHABLE"
    echo
done
```

### 2. Hypothesis Generation [L3 — full reasoning, exhaustive]

List possible root causes sorted by probability. Each with a verification method:

| # | Hypothesis | Likelihood | Verify by |
|---|-----------|:----------:|----------|
| 1 | Route path never registered (code mismatch) | 🔴 High | `grep` the decorator |
| 2 | Middleware or static mount shadowing routes | 🟡 Medium | Check ordering |
| 3 | Request schema mismatch (Pydantic rejection) | 🟡 Medium | Check payload format |
| 4 | Old process still running (change didn't deploy) | 🟢 Low | `ps aux` vs file timestamp |
| 5 | Service version mismatch (disk vs running code) | 🟢 Low | Compare `/proc/PID/cwd` |

### 3. Verification [L2 — standard reasoning]

Prove each hypothesis with the cheapest test first (curl, grep, read code).

### 4. Fix [L2 — standard reasoning]

Minimum diff. Back up the file first:

```bash
cp server.py server.py.bak.$(date +%s)
```

Two common fix patterns:

**A. Alias route (frontend compatibility):**
```python
@app.post("/api/short-path")
async def alias_fn(req: RequestModel, user_id: str = Depends(get_current_user)):
    """Alias → /api/real/long/path"""
    return await real_handler(req, user_id)
```

**B. Add/update route decorator:**
```python
@app.post("/api/correct-path")
async def handler(req: RequestModel):
    ...
```

### 5. Regression [L1 — fast, all endpoints]

Test the fixed endpoint plus ALL other endpoints:

```bash
# The previously-failing endpoint (MUST pass)
curl -s -X POST http://localhost:8001/api/fixed-endpoint -H "Content-Type: application/json" -d '{"message":"test"}'

# All other critical endpoints (MUST NOT regress)
curl -s http://localhost:8001/api/status
curl -s http://localhost:8001/api/providers
curl -s -X POST http://localhost:8001/api/chat/ask -H "Content-Type: application/json" -d '{"message":"test"}'
curl -s -X POST http://localhost:8001/api/chat/committee -H "Content-Type: application/json" -d '{"message":"test","k":1}'
curl -s http://localhost:8001/api/search/status
# Include 90s timeout scenario for long-reasoning endpoints
```

### 6. Report [L1]

Root cause (one sentence) → Evidence → Diff → Verification results → Rollback command.

## Thinking Strength Routing Table

| Level | When | API Setting | Behavior |
|-------|------|-------------|----------|
| L1 Quick | Reconnaissance, health check, regression | `thinking: false` | Mechanical, direct output, no reasoning chain |
| L2 Standard | Single root cause fix, writing diff | `thinking: true` | Standard reasoning |
| L3 Deep | Hypothesis generation, cross-module failure, repeat failure | `reasoning_effort: high` | Exhaustive hypothesis space |

**Upgrade rule:** Same root cause fails verification ≥2 times → force L3. L1 step finds anomaly → stop, escalate to L2.

## Constraints

- NO code modification without step 3 verification
- One root cause per round; batch only for truly independent fixes
- Backup original file before modification
- Always include rollback command in report
- DO NOT change existing endpoint paths or response schemas (frontend depends on contract)
- If root cause cannot be located, output `Cannot diagnose` + list of eliminated hypotheses — no speculative fixes

## Verification

Minimal check that the skill is being followed correctly:
- Report format includes: root cause → evidence → diff → verification → rollback
- Thinking strength declared at start of each step
- Backup exists before any write
