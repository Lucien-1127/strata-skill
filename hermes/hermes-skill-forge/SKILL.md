---
name: hermes-skill-forge
description: Automatically turn repeated tasks into reusable Hermes Skills.
version: 0.1.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Skill Forge, Automation, Self-Improvement]
---

# Hermes Skill Forge

Automatically observe the agent’s own behavior, extract reusable patterns, write a SKILL.md, test it in a sandbox, refine until quality ≥ 0.8, and publish it to the agentskills.io marketplace. The process uses Hermes’ memory, skills, execute_code, and subagents, and relies only on standard Python packages (no OS‑specific calls, no GPU training, no automatic merges without human review).

## When to Use

- Notice yourself repeatedly performing the same task in Hermes and want to automate it as a Skill.
- Want to contribute a new Skill to the Hermes Skill Marketplace without manual scaffolding.
- Need a self‑improvement loop that writes, tests, and publishes Skills on demand.

## Prerequisites

- Hermes Agent installed (with memory, skills, execute_code, subagents available).
- Python 3.9+ and pip.
- LLM API key configured in Hermes (e.g., `OPENROUTER_API_KEY` in environment or Hermes config).
- Optional: Docker engine if you wish to run the full Atropos RL training loop locally.

## How to Run

Invoke through the `terminal` tool: clone the repository, install dependencies, then run the demo or import the environment.

## Quick Reference

| Command / Action | Purpose |
|------------------|---------|
| `git clone https://github.com/Lethe044/hermes-skill-marketplace.git` | Obtain the Forge codebase |
| `cd hermes-skill-marketplace && pip install -r requirements.txt` | Install Python deps (openai, rich, etc.) |
| `python demo/demo_skill_forge.py --task web-summarizer` | Run a demo skill‑creation flow |
| `python -m pytest tests/ -v` | Execute the test suite |
| `from environments.skill_forge_env import skill_forge_env; skill_forge_env()` | Programmatic smoke test (see docs) |

## Procedure

### 1. Obtain the Forge repository
```bash
git clone --depth=1 https://github.com/Lethe044/hermes-skill-marketplace.git
cd hermes-skill-marketplace
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
*(Installs `openai`, `rich`, and pytest for testing.)*

### 3. Point the Forge at your Hermes agent
The Forge automatically reads Hermes’ memory and skills from `~/.hermes/`. No extra configuration is needed unless you store Hermes elsewhere; in that case set the environment variable `HERMES_PATH` to your Hermes root.

### 4. Run a demo task (creates, tests, and publishes a Skill)
```bash
python demo/demo_skill_forge.py --task web-summarizer
```
The script will:
- Search memory and the marketplace for existing similar skills.
- Write a new `SKILL.md` under `~/.hermes/skills/<task>/`.
- Create three test cases (happy, edge, error) and run them via `execute_code`.
- Compute a quality score; if ≥ 0.8 it simulates a pull request to `agentskills.io`.
- If the score is < 0.8, it spawns subagents to rewrite the skill and retries (up to a configurable limit).

### 5. Inspect the created Skill
After a successful run, the new Skill appears in:
```
~/.hermes/skills/<task>/SKILL.md
```
You can view it with `skill_view(name='<task>')` or `read_file(path='~/.hermes/skills/<task>/SKILL.md')`.

### 6. (Optional) Run the full test suite
```bash
python -m pytest tests/ -v
```
This validates the Forge’s internal logic.

### 7. (Optional) Use as a library in your own workflows
Import `skill_forge_env` from `environments.skill_forge_env` and call it with a custom task description to integrate Skill forging into larger automation.

## Pitfalls

- **External LLM cost** – The Forge queries an LLM to evaluate skill quality and generate improvements; each run consumes tokens proportional to the number of test cases and refinement iterations.
- **No automatic merge to `main`** – All published skills appear as simulated pull requests; a human must approve and merge them into the actual marketplace repository.
- **Docker required for full Atropos RL** – The reinforcement‑learning component that optimizes the reward function over many epochs needs a Docker daemon; if Docker is unavailable, the fallback is a simpler heuristic refinement loop.
- **Memory duplication guard** – The Forge searches existing skills and memory before writing; however, extremely similar tasks may still produce near‑duplicate SKILLs if the semantic similarity threshold is not met.
- **Python version mismatch** – Some Hermes installations may use a virtual environment; ensure the `pip install` target matches the Python used by Hermes.

## Verification

Run the demo and confirm that a new Skill directory is created and that the console output contains a line similar to:
```
[ AUTO EVALUATOR ] → quality_score=0.85 ✓ - calling publish_skill
```
and that the file `~/.hermes/skills/web-summarizer/SKILL.md` exists with proper YAML frontmatter and procedural steps.

*模型：deepseek-v4-flash*