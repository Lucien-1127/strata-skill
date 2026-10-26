# Marketplace Readiness & Closeout Ledger

> Scope: `Lucien-1127/strata-skill` active SKILL.md inventory. Date: 2026-10-26. This ledger is a **review record**, not a certification or proof of sales.

## Evidence baseline

| Measure | Verified state | Source |
| --- | --- | --- |
| Active skill specifications | 142 (plus 1 archived) | Recursive GitHub tree; `tools/generate_catalog.py` |
| Blocking findings in static SKILL.md scan | 0 after fixing a false positive | GitHub Actions full-library audit |
| Outstanding static warnings | 197 after targeted documentation fixes | GitHub Actions audit, subject to later changes |
| Missing explicit verification sections | 104 | Static heading check, not evidence of runtime failure |
| Missing versions | 88 | Static frontmatter check |
| Download-to-shell review warnings | 2 (both quoted blocked-command examples) | Pattern scan; manually reviewed contextual examples |
| Root-level non-catalog files | 3 | Root-only warning; **never packaged** |
| Marketplace packaging smoke test | PASS for `prompt-factory` | GitHub Actions 3.11 / 3.13 |
| Regression suite | 10 tests PASS on Python 3.11 and 3.13 | `tests/test_marketplace_readiness.py` |
| Real Hermes / Claude Code / Cursor execution | **NOT VERIFIED** | Separate real-agent acceptance required |
| Agensi seller approval, payouts, and sales | **NOT VERIFIED** | External platform account / manual approval required |

**Interpretation:** A green CI result means that the current *static security blockers, catalog synchronization, packager smoke test and ten helper regression tests* pass. It does **not** certify all 142 skills as production-ready or marketable.

## Auditing roles and handoff contract

Use distinct review functions in this order. These are **logical roles and reproducible steps**, not a claim that independent agents have run.

| Role | Responsibility | Evidence required to advance |
| --- | --- | --- |
| Inventory | Enumerate active skills and resources | Generated catalog, exact count |
| Security | Detect secrets, unsafe commands, personal artifacts, unexpected payloads | JSON report, blocking findings handled |
| Quality | Check names, descriptions, versions, links, prerequisites and examples | Skill-level checklists and test outcomes |
| Adversarial reviewer | Try missing data, conflicts, tool absence, permission denial, and unsafe instructions | Regression cases with expected outputs |
| Release packager | Build only approved skill directories | ZIP manifest, SHA-256, no repo-root private assets |
| Independent acceptance | Test with actual agent/runtime and inspect output | Logs, screenshots or reproduction notes |
| Human owner | Approve licence provenance, high-impact changes and marketplace publication | Explicit approval and marketplace outcome |

### Closure status vocabulary

Every defect must end in exactly one honest status:

- `verified_fixed`: change landed in branch, test passed, non-regression demonstrated.
- `false_positive_verified`: investigated with evidence; detector updated and regression added.
- `open`: diagnosed but not repaired or not verified.
- `blocked`: requires credentials, marketplace account, runtime or owner decision.
- `rejected_by_review`: attempted remedy failed verification; cannot be promoted.
- `not_applicable`: justified out of scope with reviewer rationale.

**Do not count `open`, `blocked` or `not_applicable` as fixed.** A failed test returns to diagnosis. A second consecutive failed repair should stop automatic changes and escalate to manual review; no silent changes to grading thresholds.

## Specific findings and closeout

| ID | Priority | Finding | Action / evidence | Status |
| --- | --- | --- | --- | --- |
| C-01 | P0 | README's `139` claim and 52 listed items diverged from the actual catalog | Bilingual README replaced; catalog generated from 142 active paths; CI enforces synchronization | `verified_fixed` |
| C-02 | P0 | Whole-repository ZIP would mix unrelated skills and personal files | Allowlist packager built; tests verify root PDF never enters a selected skill ZIP | `verified_fixed` for packager; PDF review `open` |
| C-03 | P0 | Legacy self-evolution skill asserts features not proven in current master | Existing draft PR #2 proposes evidence-based correction; no automatic merge | `open` |
| C-04 | P1 | Private-key *example* triggered the first scan's blocker | Reviewed file context; tightened detection to complete PEM blocks; regression test added | `false_positive_verified` |
| C-05 | P1 | `prompt-factory` help described v8.2 while header was v8.3 | Version text corrected | `verified_fixed` |
| C-06 | P1 | Prompt-factory prescribed unapproved automatic skill modification | Requires explicit approval, diff and regression evidence before persistent change | `verified_fixed` for rule text, runtime `open` |
| C-07 | P1 | Broken/placeholder markdown links | Repaired 4 incorrect markdown links | `verified_fixed` |
| C-08 | P1 | Remote installer piped into a shell in a dependency note | Removed download-to-shell one-liner; owner must follow official and reviewed install instructions | `verified_fixed` |
| C-09 | P1 | 104 skills without explicit verification heading | Requires individual test evidence, not empty autogenerated headings | `open` |
| C-10 | P1 | 88 skills without version frontmatter | Needs reviewed semantic version baseline per skill | `open` |
| C-11 | P1 | Possible functional duplication in FastAPI diagnostics | Compare behaviors, canonicalize documentation and preserve compatibility | `open` |
| C-12 | P0 | Third-party provenance and public MIT licensed skill commercial value unverified | Review origins and differentiation before paid sale | `blocked` on provenance review |
| C-13 | P0 | Actual agent compatibility and marketplace approval not demonstrated | Run end-to-end agent tests and submit only with creator approval | `blocked` on external runtime/account |
| C-14 | P0 | Contract PDF tracked in repository root | Excluded by ZIP builder; check contents, publishing suitability, and git history separately | `open` |

## Agensi eligibility and release gates

Agensi's published documentation says: one SKILL.md skill or a pack of at most 50 skills per ZIP; security/AI/human review; original or appropriately licensed work; successful operation on claimed agents. Official documentation: https://www.agensi.io/docs/packaging and https://www.agensi.io/docs/review-and-approval.

A listing is **GO** only if its own `SKILL.md` and bundled resources have passed the packager, the required skills have real execution evidence, licensing has been reviewed, permissions are disclosed, and the owner approves submission. Otherwise label **NO-GO**, even if the repository's overall CI is green.

### Pilot proposal: Prompt Factory

- Product framing: turn fuzzy tasks into prompts and agent-skill specifications with a self-check process.
- Target: one stand-alone ZIP produced by `tools/build_agensi_pack.py`.
- Disclosure: beta, templates bundled, may require human review, no independent benchmark of generated quality.
- Acceptance examples: incomplete intent, model/tool mismatch, unsafe instruction attempt, invalid output specification, regression against a baseline prompt.
- **Current status: PREPARATION ONLY**. A packaging smoke test passes, but real-world agent performance and commercial differentiation have not been verified.

## Commands

```bash
python -m unittest discover -s tests -p 'test_marketplace_*.py' -v
python tools/generate_catalog.py --check
python tools/audit_skills.py --root . --json /tmp/strata-audit.json --markdown /tmp/strata-audit.md --fail-on-blockers
python tools/build_agensi_pack.py --root . --out /tmp/agensi-prompt-factory.zip prompt-factory
```

**Release authority:** PR review and human approval are required. No force push, no branch-history rewrite, no deletion of a potentially personal document, no unsupported claim of multi-agent compatibility, and no seller submission within this work package.

## 中文總結

本次**流程閉環**已建立：發現缺陷、保留測試紀錄、修正偵測器及文件、執行回歸測試、重新驗收、留存尚未解決的項目。**產品閉環尚未完成**：104 項缺少明確驗證章節、88 項缺少版本，以及授權、實機相容性與 Agensi 正式上架仍需個別處理。不得把「自動化流程通過」解讀成「整個技能庫已具備商用品質」。
