# Agensi Pilot Proposal — Prompt Factory

> Draft for creator onboarding and technical review. No public listing is claimed. Pricing, runtime compatibility and actual outputs require evidence before submission.

## Listing identity

**Working title:** Prompt Factory — Prompt & Agent Skill Specification Architect

**Proposed summary (under 300 characters):**
Transform incomplete requests into structured prompts and reusable SKILL.md specifications. Includes task classification, model-aware formatting, change review, explicit quality checks and bounded iteration. Human approval required for persistent skill changes.

**Category positioning:** Prompt engineering; agent workflows; developer productivity.

**Keywords:** prompt-engineering, skill-authoring, prompt-review, structured-output, agent-design, requirements, workflow, quality-gates, specification, iteration.

## Customer problem

Users often describe a goal without a clear input contract, stop condition, or testable output. The resulting AI prompt can appear convincing but fail when reused or when required tools are missing.

## What is included

- `prompt-factory/SKILL.md` — task classification, creation/review flow, quality questions, safety limits.
- `prompt-factory/references/` — associated prompt templates and examples.
- No private data, credentials, payment links or bundled third-party executables.
- SHA-256 and complete ZIP file manifest are printed by `tools/build_agensi_pack.py`.

**What is not included:** a hosted model, proprietary APIs, paid benchmark service, model weights, guaranteed quality score, external certification or live autonomous agent runtime.

## Example requests (acceptance scenarios, NOT tested demonstrations)

1. "Convert this vague brief into an executable prompt, explaining any assumptions."
2. "Turn a developer support workflow into a SKILL.md with input/output contracts and clear stopping conditions."
3. "Review this prompt for missing permissions, unsafe tool use and unverifiable claims."
4. "Rework an existing prompt while preserving its purpose and show a change summary."
5. "The requested tool is unavailable. Provide a fallback or state that the task is blocked instead of pretending to act."

Do not publish screenshots or numerical improvement claims until these scenarios have reproducible before/after recordings on a real agent.

## Permission and compatibility disclosures

- Current repository context: originally written for Hermes Agent.
- Other agent platforms: **not yet independently verified**. Do not advertise Claude Code, Cursor or Copilot support without performing integration tests.
- External network and API keys: not required to read the skill documents, but may be needed for user-supplied tool integrations.
- Persistent modification: requires user review/approval of diff, regression proof and rollback path.
- Known limitation: internal quality scores are *heuristic self-assessments*, not proof of independent benchmark performance.

## Preflight release gate

| Gate | Requirement | Current state |
| --- | --- | --- |
| A | SKILL.md with name/description and included references | Structural scan ready |
| B | Secure, allowlist-only ZIP and deterministic digest | GitHub CI smoke test passes |
| C | Source provenance and derivative licence approval | Open |
| D | Actual behavior on promised agent runtime | Open |
| E | Negative tests and customer acceptance transcript | Open |
| F | Agensi creator enrollment and seller payout | Requires owner's account |
| G | Manual submission, review, and any resubmission | Not started |

**Decision: NOT READY TO SUBMIT AS PAID PRODUCT.** A free public preview may be considered only after gates C–E are verified and the owner approves publication.

## Partnership discussion with Joeri

Propose a **one-skill pilot**. Ask whether Agensi can share category search interest, appropriate permissions disclosures, prior examples of successful developer workflow listings, and whether a small curated launch can receive onboarding feedback.

Prefer measurable goals: listing approved, installs/loads reported, honest customer feedback, and a documented next revision. Traffic estimates alone are insufficient evidence of a likely sale.
