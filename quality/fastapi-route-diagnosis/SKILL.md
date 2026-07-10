---
name: fastapi-route-diagnosis
description: 假設驅動診斷法 — 先驗證後修改的 FastAPI 路由問題排查流程，含強度路由表
status: draft
---

# FastAPI Route Diagnosis Protocol

## 📖 Description

For diagnosing and repairing FastAPI routing issues using a hypothesis-driven approach: locate the fault → minimal modification → verify → report. Includes effort-level routing for token optimization.

## When to Load

- User reports 404/500 on a FastAPI endpoint
- Frontend calls to `/api/*` return unexpected errors
- Service migration or nginx routing changes need validation
- User provides a structured diagnostic prompt/playbook

## Protocol

### Effort Level Routing

Before each step, declare the effort level. Calling L3 for a mechanical step wastes tokens.

| Level | Steps | Behavior |
|:------|:------|:---------|
| L1 快速 | 偵察、健康檢查、迴歸驗證 | No reasoning chain, just execute |
| L2 標準 | 單根因修復、diff 撰寫 | Standard reasoning |
| L3 深度 | 假設生成與排序、跨模組故障、確診失敗後重分析 | Full reasoning; exhaustive hypothesis space |

**Rules:**
- Same root cause failing verification ≥2 times → force L3
- L1 step detects anomaly → stop, upgrade to L2, re-evaluate
- Never do root cause judgment in L1

### Execution Flow

#### Step 1: Reconnaissance〔L1〕

Read router definitions, middleware, dependency injection. Output the actual registered route table.

```
Method  Path                     Handler
GET     /api/status              status()
POST    /api/chat/ask            chat_ask()
POST    /api/chat/committee      chat_committee()
...
```

**Key checks:**
- Compare known endpoints (from user/input) vs actual registered routes
- Check middleware order (CORS → static → routes)
- Verify file timestamps match running process

#### Step 2: Hypothesis〔L3〕

List possible root causes sorted by probability, each with verification method.

| # | Hypothesis | Probability | How to Verify |
|---|-----------|:-----------:|---------------|
| 1 | Route doesn't exist — frontend calls path X but backend registers path Y | 🔴 High | Read route decorators |
| 2 | FastAPI route loading order — middleware/static mount shadows routes | 🟡 Low | Check middleware order |
| 3 | Request schema mismatch — POST payload format rejected | 🟡 Medium | curl with correct payload |
| 4 | Running old code — disk file differs from running process | 🟢 Low | Check /proc/PID path |

#### Step 3: Verify〔L2〕

Validate each hypothesis with the lowest-cost method (curl / unit test / log check).

```bash
# Health check first
curl -s http://127.0.0.1:8001/api/status

# Test each known endpoint
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://127.0.0.1:8001/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'
```

**Critical: Do NOT modify any code before step 3 verification.**

#### Step 4: Fix〔L2〕

Minimal diff. Back up original file first. Do NOT touch unrelated code.

```python
# Example: adding alias routes (preserves existing paths)
@app.post("/api/chat")
async def chat_alias(req: ChatRequest, user_id: str = Depends(get_current_user)):
    """Alias → /api/chat/ask"""
    return await chat_ask(req, user_id)
```

**Constraints:**
- Fix ONE root cause at a time; multiple issues → batch in separate rounds
- Never change existing endpoint paths or response schemas
- Back up before editing; report must include rollback command

#### Step 5: Regression〔L1〕

Re-run trigger test + check ALL endpoints (including 90s long-inference timeout scenarios).

Test every endpoint with real curl:
```bash
for endpoint in /api/status /api/providers /api/chat/ask /api/chat/committee /api/search/status /api/chat/history; do
    curl -s -o /dev/null -w "$endpoint → %{http_code}\n" http://127.0.0.1:8001$endpoint
done
```

#### Step 6: Report〔L1〕

Markdown report with:

```markdown
## Root Cause (one sentence)

## Evidence

## Diff

## Verification Results (command + actual output)

## Risk & Rollback

`cp /path/to/backup /path/to/original`

## Effort Stats

| Step | Level |
|:-----|:------|
| Recon | L1 |
| Hypothesis | L3 |
| Verify | L2 |
| Fix | L2 |
| Regression | L1 |
```

### When Unable to Diagnose

Output "Unable to diagnose" + list of excluded hypotheses. Never make speculative fixes.

### Common Pitfalls

- ❌ Modifying code before verification (step 3). The user's protocol explicitly forbids this.
- ❌ Changing endpoint paths that frontend zxFetch depends on. The contract is: "frontend sends path X → backend must respond at path X."
- ❌ Not restarting the server after fix. Old process may still hold the port and serve old code.
- ❌ Forgetting to clear `.pyc` cache — Python may serve cached bytecode.
- ❌ Running L3 for mechanical L1 tasks (wastes tokens).
- ❌ Skipping backup. Always `cp file.py file.py.bak.$(date +%s)` before any edit.

### Quick Rollback Commands

```bash
# Server restart with port kill
sudo pkill -f server.py 2>/dev/null; sleep 2
python3 /opt/path/to/server.py &

# Restore from backup
cp /opt/path/to/server.py.bak.TIMESTAMP /opt/path/to/server.py

# Verify port is listening
ss -tlnp | grep 8001
```

## Relations

- `verification-before-completion` — General delivery verification (complementary: codebases vs service endpoints)
- `project-architecture-audit` — Codebase architecture review (deeper than route-level)
