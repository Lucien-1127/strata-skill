---
name: feg-state-hook-architecture
description: "Embed FEG/State Machine/Hook patterns into SKILL.md."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Skill-Architecture, FEG, State-Machine, Hook, Workflow-Design]
---

# FEG / State Machine / Hook — Skill Architecture Patterns

Skills are not just documentation — they are the **carrier of execution logic**.
FEG (Finite Execution Graph), State Machine, and Hook are three complementary
patterns that can be embedded directly into a skill's structure.

The relationship between the three:

```
Hook (event)         →  SKILL.md Prerequisites / Pitfalls / Verification
State Machine (state) →  Procedure steps with condition branches
FEG (flow graph)     →  Multi-skill orchestration + delegate_task dispatch
```

## When to Use

- A task follows a **multi-step flow** with condition branches → structure it as a State Machine in Procedure
- A task repeats a **known failure pattern** → add a Hook in Pitfalls / Verification
- A task involves **multiple skills chained together** → design it as an FEG
- User corrected the same behavior multiple times → that correction belongs in the skill, not in memory

## The Three Patterns in SKILL.md

### 1. Hook Pattern (Event Layer)

**Where in SKILL.md:** `## Prerequisites`, `## Pitfalls`, `## Verification`

Hooks are **guardrails and checkpoints** that fire at specific points:
- Before execution (Prerequisites): check env vars, credentials, dependencies
- During execution (Procedure step): data validation hooks
- After execution (Verification): curl real API, confirm output
- Error handling (Pitfalls): known failure workarounds

**Example — self-correction hook:**

```markdown
## Verification（with self-correction hook）
驗證發現錯誤後，必須立即將學到的教訓寫回技能：
1. 判斷：這個錯誤我之前犯過嗎？
   - 是 → 為什麼沒攔住？SKILL.md 缺了什麼？補上後才算修好
   - 否 → 會不會再犯？會就加到 Pitfalls
```

### 2. State Machine Pattern (State Layer)

**Where in SKILL.md:** `## Procedure`

Each numbered step is a state transition:

```
1. Check prerequisites        → idle → ready
2. Execute main logic         → ready → running
3. Self-verify results        → running → verified
4. Mark complete              → verified → done
5. Rollback on failure        → running → rollback → idle
```

**Condition branches** in the text:

```
- If API returns 200: proceed to step 3
- If API returns 401/403: log new key, go back to step 1
- If time out: mark as BLOCKED, report to user
```

### 3. FEG Pattern (Flow Layer)

**Where in SKILL.md:** Implicit in multi-skill orchestration via `delegate_task`

An FEG is a directed graph of skills:

```
User Request
  → [routing skill] decide provider
     ├→ A path: [agnes-gen] → [media-pipeline] → [qc-skill]
     └→ B path: [deepseek-reason] → [output]
```

In SKILL.md, document the graph as a section header or procedure that calls other skills:

```markdown
## Orchestration Flow

1. [skill: routing-strategy] determines provider based on availability
2. [skill: ai-provider-deep-research] gathers data
3. [skill: content-expander] formats output
4. [skill: verification-before-completion] validates result
```

## Pitfalls

- **Don't over-abstract**: Not every skill needs all three patterns. Use the one that fits the problem.
- **Hooks must be checkpoints, not just comments**: A Verification section that says "check manually" is not a hook — it needs a concrete command to run.
- **State Machine steps must be verifiable**: Each step should have a measurable exit condition.
- **FEG must stay at skill-call level**: Don't inline the full logic of subordinate skills in the orchestrator.
- **Self-correction is a Hook, not a separate skill**: When you discover an error pattern you've made before, the fix is to update the relevant skill's Pitfalls or Verification section — not to create a standalone "error-correction" skill. Embed the lesson back into the skill that governs the task.
- **All three patterns can coexist in the same SKILL.md**: A skill's Procedure is a State Machine, its Pitfalls are Hooks, and its cross-skill references form an FEG. Not mutually exclusive — complementary layers of the same document.

## User Insight (from session 2026-07-08)

User corrected: "技能也能插入這些邏輯啊 — 平常重複錯的當正確了也能修改這個邏輯，或是流程也能用這個。"

Skills ARE the carrier of execution logic, not passive documentation. Self-correction is embedded in the skill itself — when verification finds a known error, the skill gets patched immediately as part of the task.

## Verification

A well-structured skill should be readable as:
1. A checklist of preconditions (Hook)
2. A sequence of steps with decision points (State Machine)
3. A clear picture of how it connects to other skills (FEG)
