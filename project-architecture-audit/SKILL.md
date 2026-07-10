---
name: project-architecture-audit
description: "Deep analysis of project codebases — architecture review, dependency verification, SDK compatibility checks, production-"
---
# project-architecture-audit

## 📖 Description

Deep analysis of project codebases — architecture review, dependency verification, SDK compatibility checks, production-readiness assessment, and prioritized optimization recommendations. Emphasizes practical honesty over surface observations.

---

# Project Architecture Audit

## Core Principle: 實用性優先 (Practicality First)

This user explicitly values **深度研究 實用性** — deep, verified, honest analysis over surface-level observations. Every audit must answer one question: **"Would this work in the real world, and if not, what's the real blocker?"**

Do NOT:
- List every eslint warning or minor code style issue
- Suggest nice-to-have refactors without linking them to a practical problem
- Give generic advice that could apply to any project
- Accept code at face value — verify dependencies, SDK compatibility, architecture claims

DO:
- Identify what will actually break in production
- Check dependency versions against real docs (not just package.json)
- Verify SDK initialization parameters match actual API
- Test the critical path — would the core flow actually work?
- Give a clear "can I use this?" verdict

## Methodology

### Phase 1: Full Surface Scan
1. `search_files(pattern="*", target="files")` to get the full file tree
2. README.md first — note any disclaimers ("prototype only", "not for production")
3. All manifest files: package.json, tsconfig.json, Cargo.toml, pyproject.toml, etc.
4. Entry points: index.tsx, App.tsx, server.js, main.py, etc.

### Phase 2: Identify Project Origin
Look for telltale signs of generated/scaffolded projects:
- `@license` headers from a cloud provider (Google, AWS, Azure)
- README stating "not intended for production"
- Auto-generated `.env.local` or `.env.example` files
- Generic package.json with `"latest"` versions
- "Get Code" or "Export" artifacts

**Critical sub-check for cloud-exported projects:** Read `.env.local` (via terminal `cat`, not `read_file` which blocks .env). The project ID / region in there is often a **sample or throwaway project** created by the export tool, NOT the user's real cloud project. Flag this mismatch explicitly — ask the user to verify their actual project ID from Cloud Console before proceeding.

### Phase 3: Dependency Audit
1. Check ALL package.json files for `"latest"` version specifiers — flag them
2. Cross-check each dependency's actual API:
   - Search web for the npm package page
   - Verify the import statements match the documented API
   - Check for Node.js version requirements vs installed version
   - Flag deprecated or redundant deps (`node-fetch` on Node 18+, CDN packages, etc.)
3. Check for peer dependency conflicts (e.g., React 19 vs SDK requiring React 18)

### Phase 4: Architecture Flow Verification
1. Trace the data flow: User Input → Component → Service → Network → Backend → External API
2. Identify each "seam" where the flow could break:
   - **Authentication**: How does each layer authenticate? Are there hardcoded secrets?
   - **URL routing**: Are there URL interceptors, proxy configurations, or path matchers?
   - **Error handling**: What happens when each layer fails?
   - **State management**: Is state persisted? What happens on page refresh?
3. Check for global patches (e.g., `window.fetch` overrides, monkey-patches) — these are high-risk

### Phase 5: Production-Readiness Assessment
For each finding, classify:

| Severity | Meaning | Example |
|----------|---------|---------|
| 🔴 **Fatal** | Will break in production/on upgrade | Fake API keys, SDK init with wrong params |
| 🟠 **High** | Fragile, hard to debug when it fails | Global fetch interceptors, hardcoded secrets |
| 🟡 **Medium** | Missing infrastructure | No persistence, no error boundaries |
| ⚪ **Low** | Quality of life | No tsconfig, CDN deps miscoded |

### Phase 6 (Extended): Cloud Infrastructure Audit

When the app depends on cloud services (Vertex AI, Compute Engine, Cloud SQL, etc.), extend the audit beyond code:

1. **Enabled APIs** — `gcloud services list --enabled`.
2. **Actual resources** — VMs, databases, buckets, clusters, run services.
3. **IAM policy** — Check for over-privileged users/SAs. Owner + narrower role on same user? Remove the redundant one.
4. **Auth pattern** — Is the app using a personal account for ADC? Flag it; recommend a service account.
5. **Cost optimization opportunity** — Are services running but not used? Are there newer model generations that are cheaper (e.g., Gemini 3.5 Flash at same price as 2.5 Flash)?
6. **Region compatibility** — Verify the model/resource region matches availability (Gemini 3.x requires `us` multi-region, not `us-central1`).

See `google-cloud-ai` skill → `references/gcp-service-audit.md` for the full command set.

### Phase 7: Actionable Recommendations

Format as a clear prioritized list:
1. **P0 — Must fix**: things that actively prevent the app from working
2. **P1 — Architecture**: structural issues that will cause pain
3. **P2 — Enhancement**: features missing for a complete product

Each recommendation must include:
- A concrete "how" (not just "this is bad")
- The expected improvement (bundle size, reliability, maintainability)
- A fallback option when multiple approaches exist

### Phase 8: Distinguish Local Dev from Production Deployment

**Critical trap:** The code in the repo on the user's machine may NOT be what's running in production. This session's key finding:

- **Desktop** = Vertex AI Studio export (React + Express) — experimental frontend
- **VM** = Actual production system (Python FastAPI, 60+ docs, 47K RAG entries, multi-agent)

**How to check:**
1. Look for a GCE VM: `gcloud compute instances list --project=<PROJECT_ID>`
2. If a VM exists, SSH in and check running processes: `ps aux | grep -i 'node\|npm\|python\|uvicorn\|fastapi' | grep -v grep`
3. Check listening ports: `ss -tlnp` — port 80/443/8080/7850 suggest a production server
4. Compare file counts/sizes — VM with `docs/`, `tests/`, `src/` is more likely production than a single-page export

**When to flag this:**
- README has "not for production" disclaimers
- User mentions a VM or remote server
- Code looks like scaffolding/export template (all `"latest"` versions)
- Always ask: *"Is this the actual running service, or a local development copy?"*

### Phase 9: The Honest Verdict
End with a direct, non-fluffy answer to "can I use this?":

| Scenario | Verdict |
|----------|---------|
| Local prototype/demo | ✅ Works as-is with basic setup |
| Production deployment | ❌ Do not deploy without changes |
| Production with fixes | ⚠️ Possible after addressing [P0 items] |

Include the concrete setup steps needed just to get it running locally (e.g., `gcloud auth application-default login`, `npm install`).

## Typical Deliverable Structure

```
## Overview (3-line summary)
## Project Origin (template detection)
## Data Flow (diagram or list)
## Dependency Audit (table)
## Production-Readiness (severity table)
## Recommendations (P0 → P1 → P2)
## Honest Verdict
```

## GCP-Specific Audit Additions

When auditing GCP Vertex AI projects, also check:

1. **Project origin**: Check if the project is a Vertex AI Studio "Get Code" export (identifiable by `Copyright 2025 Google LLC` headers, `vertex-ai-proxy-interceptor.js`, and README disclaimers about prototype-only use).
2. **SDK parameter validity**: Verify `enterprise: true` vs `vertexai: true` (the latter is undocumented and silently ignored). Cross-check against actual SDK version docs.
3. **Location mapping**: "global" is not a valid Vertex AI region. Must map to `us-central1` or `us` depending on model generation.
4. **Model availability**: Check model-availability-by-region docs before committing to a model name. Gemini 3.x may not be available in all regions.

## Pitfalls
- Don't assume package.json versions match what's actually available — always verify against npm/web
- Don't trust auto-generated code to have correct initialization parameters
- Don't overlook README disclaimers — they're often the most honest part of the project
- Don't forget to check the BUILD/TEST scripts exist before claiming the project is ready to run
- A project with `"latest"` on all deps is almost certainly a template/generated project, not a hand-crafted one
- Global monkey-patches (window.fetch overrides) are the single most fragile pattern in frontend projects
- **Read the user's Console output line-by-line before drawing org/resource conclusions.** When the user pastes GCP Console output, the visual tree shows indent hierarchy (No organization vs hsieh89t-org branches), project grouping, and column order. Don't flatten it into a simplified view without matching every row. If the org tree shows `No organization` → `Zhiyan-Legal-AI` and `hsieh89t-org` → `gemini-api-service`, present it exactly that way, not as 'both under the org'. The user will correct you if you get the structure wrong — avoid the correction by reading carefully the first time.

## Follow-up: Cost Optimization

After the architecture audit, if the project uses billable cloud services (VMs, Vertex AI, Cloud Storage, etc.), offer a **cost optimization pass** as the natural next step:

> *"I found [N] billable resources. Want me to run a cost optimization pass next? I can check for orphaned disks, oversized VMs, CUD eligibility, and set up budget alerts."*

This is covered by the `gcp-cost-optimization` skill (devops category).

## Cross-references

- `references/fastapi-routing-diagnosis.md` — FastAPI 路由診斷協議：假設驅動、強度路由、最小 diff 修復。用於 API 服務 404/5xx 路由故障場景。
- `gcp-cost-optimization` skill — Full cost reduction playbook after audit.
- `vertex-ai-web-integration` skill — Refactoring Vertex AI Studio exports to clean SDK-on-backend.
- `google-cloud-ai` skill — Broader GCP AI service integration (note: overlaps with `vertex-ai-web-integration`; consider consolidation).
- `ai-provider-deep-research` skill (mlops) — Separate methodology for researching AI **providers** (not codebases). Use when the research target is an AI company/model/API rather than a software project. Has complementary cross-validation, pricing analysis, and Obsidian integration workflows.

## Verification
After recommendations, offer to:
1. Fix P0 items immediately
2. Demonstrate the app running after fixes
3. Set up git and CI if repo is unversioned
4. Run a cost optimization pass as follow-up
