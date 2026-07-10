---
name: deep-research-github-repo
description: Deep-dive into any GitHub repository's architecture.
version: 0.1.0
author: Hermes
platforms: [linux, macos]
metadata:
  hermes:
    tags: [GitHub, Research, Architecture, Open-Source]
status: stable
---

# Deep Research of a GitHub Repository

Thoroughly investigate an open-source GitHub repository to understand its architecture, core components, data flow, and operational patterns. This skill produces a structured multi-section report covering stats, file structure, core files, storage, deployment, and key design decisions. It does NOT run the project's tests or deploy it — it is read-only analysis.

Dependencies: `curl`, `python3`, `git` (all std for Hermes host).

## When to Use

- "Analyze this GitHub repo and explain its architecture."
- "Do a deep dive on [repo URL]."
- "Research how [project] works internally."
- "What is the structure of [repo] and how does it fit together?"
- "深度研究這個倉庫"

## Prerequisites

- `git` installed (for cloning).
- `curl` and `python3` installed (for GitHub API and JSON parsing).
- No API tokens needed for public repos.

## How to Run

Invoke through the `terminal` tool + `read_file` in sequence:

1. Clone with `git clone --depth=1 <url>`.
2. Fetch GitHub metadata via `curl -s https://api.github.com/repos/{owner}/{name} | python3 -m json.tool`.
3. Read `README.md`, `package.json`, and key config files.
4. Explore structure with `find . -maxdepth 3` (excluding `.git` and `node_modules`).
5. Read core source files for architecture understanding.
6. Synthesize into report.

## Quick Reference

| Step | Command / Tool | Purpose |
|------|---------------|---------|
| Clone | `git clone --depth=1 <url> /tmp/<repo>` | Get latest code, not history |
| Stats | `curl -s https://api.github.com/repos/{owner}/{name}` | Stars, forks, license, topics |
| Top files | `read_file README.md` + `read_file package.json` | Identity, deps, scripts |
| Structure | `find . -maxdepth 3 -not -path './.git/*' -not -path './node_modules/*'` | Directory layout |
| Docs | `find docs/ -maxdepth 2 -name '*.md' \| head -20` | Architecture and dev docs |
| Source | `find src/ -maxdepth 2 -name '*.ts' \| head -30` | Core implementation |
| Config | `read_file plugin.json`, `.mcp.json`, `hooks.json` | Plugin/MCP integration |

## Procedure

### 1. Clone the Repository

Clone with `--depth=1` to avoid full history:

```bash
cd /tmp && git clone --depth=1 https://github.com/{owner}/{repo}.git
```

### 2. Fetch GitHub Metadata

Get stats, license, topics, language, and description via the API:

```bash
curl -s https://api.github.com/repos/{owner}/{repo} | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k in ['stargazers_count','forks_count','open_issues_count','language',
          'license','topics','default_branch','created_at','pushed_at']:
    print(f'{k}: {d.get(k)}')
"
```

Extract key fields: `stargazers_count`, `forks_count`, `license` (name/key), `topics`, `language`.

### 3. Read the README

Use `read_file` to get the full README.md — this is the primary source for:
- Project description and value proposition
- Quick start / installation
- Features list
- Configuration reference
- Architecture summary (if present)
- License and support info

### 4. Explore File Structure

Run `find` at depth 3 to understand the layout:

```bash
find . -maxdepth 3 -not -path './.git/*' -not -path './node_modules/*' | head -100
```

Look for: `src/`, `docs/`, `plugin/`, `scripts/`, `tests/`, config files (`package.json`, `tsconfig.json`, `.mcp.json`, `plugin.json`).

### 5. Read Configuration Files

Key files to inspect (in order):

| File | What it reveals |
|------|----------------|
| `package.json` | Version, dependencies, scripts, bin entries, exports |
| `.claude-plugin/plugin.json` | Plugin metadata for Claude Code marketplace |
| `plugin/.mcp.json` | MCP server definition (command, args) |
| `plugin/hooks/hooks.json` | Lifecycle hooks (Setup, SessionStart, PostToolUse, etc.) |

### 6. Read Core Source Files

Identify the main source files from `package.json` scripts and `src/` structure. Look for:

- **Entry point / worker service** — the daemon that manages the runtime
- **Storage layer** — database schema, connection, migrations
- **API routes** — HTTP endpoints the service exposes
- **Integration layer** — hooks, MCP servers, platform adapters

### 7. Read Documentation

Check `docs/` for architecture overviews:

```bash
find docs/ -maxdepth 2 -name '*.md' -not -path '*/i18n/*' | head -20
```

Read the most structural docs first (architecture, data flow, storage).

### 8. Synthesize Report

Organize findings into these sections:

1. **What it is** — one-paragraph summary from README + description
2. **Stats** — stars, forks, license, language, version, topics
3. **System Architecture** — layers, components, data flow diagram (ASCII)
4. **Core Mechanisms** — hooks, storage, search, APIs
5. **Key Design Decisions** — deduplication, graceful degradation, progressive disclosure
6. **Installation & Configuration** — from README Quick Start
7. **Strengths & Limitations** — observed from source
8. **Relevance** — what can be learned from this project

## Pitfalls

- **Large repos** may have very deep `src/` trees. Limit `maxdepth` and focus on the first 30 source files.
- **Monorepos** may have multiple `package.json` files. Check the root one first, then drill into packages.
- **Bun vs Node dependencies**: If the project uses `bun:sqlite` or Bun APIs, it cannot run on plain Node.js — note this in the report.
- **Minified/bundled source**: Some repos only publish bundled JS/CJS in a `plugin/` directory. Source TypeScript may be in a separate `src/` directory.
- **git clone depth**: Some repos redirect (GitHub mirror). If the clone URL returns HTML, use the SSH or HTTPS URL from the API response.
- **API rate limiting**: Unauthenticated GitHub API requests are limited to 60/hour. For heavy research, consider using `curl -H "Authorization: token $GITHUB_TOKEN"`.

## Verification

Confirm you have the repo cloned and metadata available:

```bash
ls /tmp/{repo}/README.md && curl -s https://api.github.com/repos/{owner}/{repo} | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('stargazers_count',0)} stars, {d.get('forks_count',0)} forks\")"
```
