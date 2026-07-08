---
name: hermes-self-evolution
description: Automatically evolve Hermes Agent skills, prompts, and tools.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [Self-Evolution, Optimization, DSPy, GEPA, Darwinian]
---

# Hermes Agent Self-Evolution System

Automatically improve Hermes Agent skills, tool descriptions, system prompt sections, and tool code using DSPy‑GEPA and Darwinian Evolver. The system runs evaluation datasets, compares baseline vs. evolved candidates, and outputs GitHub pull requests for human review. It does **not** modify model weights, require GPUs, or auto‑merge changes without approval. All operations depend on a functioning Hermes Agent installation, Python, Git, and access to LLM APIs for evaluation.

## When to Use

- Improve a specific `SKILL.md` file using reflective optimization (GEPA).
- Refine tool descriptions so the agent selects the correct tool more reliably.
- Evolve a system prompt section (e.g., reduce verbosity, improve tool‑usage guidelines).
- Fix a known bug in a tool implementation via evolutionary search (Darwinian Evolver).
- Set up a continuous self‑improvement loop that monitors skill performance and proposes upgrades.

## Prerequisites

- Hermes Agent installed (clone `NousResearch/hermes-agent` or `pip install hermes-agent`).
- Python 3.10+ with `pip` and `venv` available.
- LLM API keys configured in Hermes (OpenAI, Anthropic, etc.) – needed for `batch_runner` evaluation.
- Git installed.
- Docker Engine (required only for evolving tool code via Darwinian Evolver; optional for skill/prompt evolution).
- Approximately 2–4 hours of compute budget per evolution run (cost depends on LLM usage).

## How to Run

Invoke through the `terminal` tool: clone the evolution repository, install it, point it at your Hermes agent, then run the evolution commands.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git clone https://github.com/NousResearch/hermes-agent-self-evolution.git` | Get the evolution codebase |
| `cd hermes-agent-self-evolution && pip install -e ".[dev]"` | Install dependencies (DSPy, GEPA, etc.) |
| `export HERMES_AGENT_REPO=~/.hermes/hermes-agent` | Point to your Hermes agent checkout |
| `python -m evolution.skills.evolve_skill --skill github-code-review --iterations 10` | Evolve a skill |
| `python -m evolution.tools.evolve_tool_descriptions --iterations 5` | Evolve tool descriptions |
| `python -m evolution.prompts.evolve_prompt_section --section MEMORY_GUIDANCE --iterations 5` | Evolve a system‑prompt section |
| `python -m evolution.code.evolve_tool_code --tool file_tools --iterations 10` | Evolve tool code (requires Docker) |
| `hermes evolve deploy <target> --version <N>` | Deploy an evolved version via PR (CLI wrapper) |
| `terraform plan` *(not applicable)* | — |

## Procedure

### 1. Obtain the evolution repository
```bash
git clone --depth=1 https://github.com/NousResearch/hermes-agent-self-evolution.git
cd hermes-agent-self-evolution
```

### 2. Install the evolution package
```bash
pip install -e ".[dev]"
```
This installs DSPy, GEPA, and the Darwinian Evolver CLI (AGPL‑v3, used only for code evolution).

### 3. Point to your Hermes agent
```bash
export HERMES_AGENT_REPO=$HOME/.hermes/hermes-agent
# If you cloned Hermes elsewhere, adjust the path.
```

### 4. Evolve a skill (example: github‑code‑review)
```bash
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source synthetic   # or: sessiondb, golden, auto
```
The command:
- Wraps the target `SKILL.md` as a DSPy module,
- Generates an evaluation dataset (train/val/holdout),
- Runs GEPA optimization,
- Compares baseline vs. evolved on the holdout set,
- Creates a git branch with the improved `SKILL.md`,
- Opens a draft PR against the Hermes agent repo with before/after scores and a diff.

### 5. Evolve tool descriptions
```bash
python -m evolution.tools.evolve_tool_descriptions \
    --iterations 5 \
    --benchmark-gate tblite-fast
```
Optimizes the `description` fields in `tools/registry.py` so the agent picks the right tool more reliably.

### 6. Evolve a system‑prompt section
```bash
python -m evolution.prompts.evolve_prompt_section \
    --section MEMORY_GUIDANCE \
    --iterations 5
```
Evolves a named section (e.g., `MEMORY_GUIDANCE`, `TOOL_USAGE_GUIDELINES`, `IDENTITY`) while respecting size‑growth limits (< +20 %) and prompt‑caching compatibility.

### 7. Evolve tool code (Darwinian Evolver)
```bash
python -m evolution.code.evolve_tool_code \
    --tool file_tools \
    --bug-issue 742 \
    --iterations 10
```
Requires Docker to run the evolution CLI. The process:
- Maps the tool source file to a `GitBasedOrganism`,
- Uses a composite fitness function (`pytest` + benchmark + bug‑reproduction),
- Produces a PR with the evolved code if all tests pass and the bug is fixed.

### 8. Deploy an evolved version (human‑review step)
After any evolution command finishes, it will have printed instructions to create a PR. You can also use the helper:
```bash
hermes evolve deploy github-code-review --version 3
```
This creates (or updates) a pull request with the evolved artifact. **Human review and merge are required**—the system never pushes directly to `main`.

### 9. Set up a continuous loop (optional)
To automate detection and optimization:
```bash
# Add to crontab or Hermes cronjob:
0 3 * * * /usr/bin/hermes evolve monitor --weekly
```
The monitor runs weekly benchmarks, tracks skill‑success rates from `SessionDB`, and triggers GEPA when a failure‑rate threshold is crossed, always producing a PR for human review.

## Pitfalls

- **Docker required for code evolution** – the Darwinian Evolver runs as an external CLI (AGPL‑v3) and needs a Docker daemon to build test containers.
- **Evaluation cost** – each evolution run consumes LLM tokens via `batch_runner`; start with small eval sets (10‑20 examples) to keep costs low.
- **Prompt‑bloat guardrails** – evolved system‑prompt sections must not exceed their current size by >20 %; the optimizer applies a length penalty to discourage verbose solutions.
- **No hot‑swapping** – evolved content only takes effect on new sessions; existing conversations continue with the old version.
- **Semantic preservation** – the optimizer is constrained to keep the original intent; drastic drift is penalized in the fitness function.
- **Human‑in‑the‑loop** – all changes land as pull requests; automatic merge is disabled to prevent accidental breakage.
- **Benchmark gates** – a candidate must pass the full test suite (2550+ tests) and not regress on TBLite/YC‑Bench beyond a small tolerance (≈2 %); otherwise it is discarded.

## Verification

Run a quick evolution cycle on a low‑stakes skill and confirm that a pull request is created:

```bash
# Clone Hermes agent if you don’t have it locally
git clone --depth=1 https://github.com/NousResearch/hermes-agent.git $HOME/.hermes/hermes-agent

# Run a tiny evolution (2 iterations) on the arXiv skill
python -m evolution.skills.evolve_skill \
    --skill arxiv \
    --iterations 2 \
    --eval-source synthetic

# Check output for a line like:
#   Created PR: https://github.com/NousResearch/hermes-agent/pull/XXX
#   (or see the git branch `evolve/arxiv-<timestamp>` with commits)
```

If the command finishes without error and reports a PR/branch with an evolved `SKILL.md`, the skill is working.

*模型：deepseek-v4-flash*