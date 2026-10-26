# Agensi Listing Draft — Agent Evidence Closeout Gate

**Status:** Candidate for private creator review. Not submitted or approved by Agensi. The skill has automated validation tests, **not a real-world Agent execution certificate**.

## Product fields

**Title:** Agent Evidence Closeout Gate — Four-Gate Verification

**Summary (under 300 characters):** Stop AI agents from claiming success without recorded checks. Run a four-gate closeout review covering functionality, safety, regressions and customer acceptance, plus a local SHA-256 evidence validator that explicitly separates completed, blocked, regressed and unverified work.

**Category:** Trust & Audit / Developer Productivity

**Tags:** agent-reliability, audit, automation, quality

**Keywords:** agent-verification, evidence, regression, closeout, workflow, safety

**Version:** 0.1.0 beta

**Use cases:** Agent handoff quality control; pre-release checklist; multi-step task verification; regression and exception tracking; client-delivery review.

## The buyer's problem

An AI agent can produce plausible explanations of work that was never executed. Developers and service providers need a repeatable review procedure that refuses false completion, gives each claim a piece of inspectable evidence and keeps failed or blocked work visible.

## What the skill actually does

1. Establishes the customer's request and acceptance conditions.
2. Requires four separate outcomes: functional, safety, regression and customer acceptance.
3. Distinguishes genuine blockers and regressions from final completion.
4. Can mechanically check a JSON report's required fields, claimed check results, local evidence file paths and SHA-256 digests using Python.
5. Returns explicit outcomes: `evidence_consistent`, `unresolved` or `invalid`, with exit codes 0, 2 or 1. A consistent record does not establish independent task completion.

**Limits:** Hashes verify file integrity, not authenticity. The buyer must provide actual tool logs/evidence and review them independently. The script does not control the customer's agents, run their tests, verify remote deployments or make independent judgments.

## What is shipped

- One `SKILL.md` with structured task-closure instructions.
- `scripts/verify_closeout.py` — local-only, no third-party dependencies and no network access.
- `references/report-contract.md` — JSON report contract, error cases and Traditional Chinese notes.
- `templates/closeout-template.json` — safe starter record with all four gates unverified by default.
- Repository-side automated negative and CLI tests (available in GitHub, not required at buyer runtime).

## Permissions and disclosures

| Permission | Needed? | Purpose |
| --- | --- | --- |
| Read local file | Optional | Inspect approved JSON and attached evidence |
| Execute Python | Optional | Run read-only consistency verifier |
| Write file | Not required by validator | User/host may separately save reports |
| Network access | No | No remote services are called |
| API key or environment values | No | No API accounts required |
| Install native executable | No | Python standard library only |

Do not imply that a permission granted to the verifier also authorizes the broader agent to deploy, merge, delete, spend funds or contact third parties.

## Test evidence and launch gates

- Repository CI: Python 3.11/3.13 regression tests, catalog consistency and packaged ZIP smoke test. See PR #8 and linked Actions runs.
- Test scenarios include four passing gates, absent/changed evidence, path traversal, symlinks, failure statuses and malformed JSON.
- **Still required:** real Hermes execution on a representative customer workflow, independent reviewer inspection of the generated closeout record and the actual customer deliverable.
- **Not yet obtained:** Agensi approval, customer feedback, third-party compatibility tests, payout account validation or sales.

## Differentiation from existing Agensi skills

There is already a separate Agensi product named `Agent Reliability Audit` by another creator, as well as other agent audit products. **Do not use that exact title, slug, or imply an endorsement, derivative relationship, or exclusivity.** This candidate is instead `Agent Evidence Closeout Gate`: a narrowly scoped, mechanical closeout-contract validator for local evidence files, explicit four-gate completion claims, and deterministic invalid/blocked outcomes. It does not analyze full distributed traces, benchmark model quality, or replace those other products.

## See it in action — illustrative scenario, not a customer testimonial

**Request:** "Our agent claims the deployment is complete, but the safety verification evidence was modified after the run. Check whether the completion record is internally consistent, without contacting the deployment or making any changes."

**Inputs:** One report JSON declaring `completed`, including the four checks (functional, safety, regression, customer), and four approved local evidence files. The expected safety file hash in the report is from an earlier version, but the actual current file bytes differ.

**Expected operation:** Use `scripts/verify_closeout.py --report ... --evidence-root ...`. The validator reads local evidence, recomputes each SHA-256, and refuses the completion claim when the stored safety digest does not match the actual file. It does not overwrite evidence, run arbitrary commands or silently resubmit deployment changes.

**Expected result:** JSON `{"verdict":"invalid", "exit_code":1, ...}` with a `check[...]: evidence checksum mismatch` finding. The agent's final report must say that the record is inconsistent, state which gate needs a fresh authoritative log, and request independent review. This scenario is covered by automated regression tests, **but the paragraph above is not a transcript of a live customer deployment**. Actual Agent runtime demonstration must be captured before publishing the listing as a proven integration.

## Pricing experiment — proposal, not a claim of market prices

Start with a **free introductory listing** to measure real skill loads and feedback, subject to Agensi creator review. Consider a paid extended version only when there is materially differentiated functionality, verified customer demand and a clear maintenance commitment. Do not sell a cosmetically repackaged copy of freely available material as though it were exclusive.

## Joeri / onboarding discussion

Ask for review of this specific one-skill pilot, not a generic promotion promise. Useful questions: whether this scope addresses the platform's current Trust/Audit demand, whether text-only Python verification is appropriate for their agents, and what disclosure/quality additions would improve approval likelihood.

Official marketplace packaging and review guidance:
- https://www.agensi.io/docs/packaging
- https://www.agensi.io/docs/review-and-approval

---

## 繁體中文摘要

正式商品方向為「Agent 工作結果稽核」。可用於 AI 接案與多代理交付：必須逐項查核功能、安全、回歸及客戶驗收結果，不得只憑模型自評宣布完工。這個候選版本有實際 Python 驗證工具，但不能證明證據內容真實、也尚未完成外部平台審核；正式上架前仍須實機測試與核准。
