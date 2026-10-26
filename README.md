# Strata Skill — AI Agent Skills Library

**142 active skill specifications** for planning, prompt engineering, developer workflows, research, legal-document workflows, and quality control. The repository is primarily developed for **Hermes Agent**. A skill's presence in this library **does not** mean it has been independently tested on every agent platform.

[Complete, generated skill catalog](docs/SKILL_CATALOG.md) · [Quality and marketplace readiness](docs/MARKETPLACE_READINESS.md) · [MIT license](LICENSE)

## What you can do

- **Design reusable workflows:** turn ambiguous requirements into concrete agent instructions, review checkpoints, and stopping conditions.
- **Build and review prompts:** structured creation, iteration, and assessment with explicit assumptions.
- **Improve developer operations:** documented diagnostics, deployment procedures, and quality gates.
- **Work on domain-specific tasks:** legal and research skills with a requirement for verification and human oversight.

**Featured pilot:** [Prompt Factory](prompt-factory/SKILL.md) — a beta skill for generating and reviewing prompts and agent-skill specifications. It uses bundled templates; its evaluation scores are self-assessments, **not independent benchmark results**.

## Quick start

Requirements: Git, Python 3.11+ for the audit/package helpers, and a compatible AI agent for skill execution.

```bash
git clone https://github.com/Lucien-1127/strata-skill.git
cd strata-skill

# Inspect the complete active catalog
python tools/audit_skills.py --root . --json /tmp/strata-audit.json --markdown /tmp/strata-audit.md

# Build an allowlist-only ZIP with just one selected skill
python tools/build_agensi_pack.py --root . --out /tmp/agensi-prompt-factory.zip prompt-factory
```

**Hermes Agent (manual installation example):** Keep this repository outside the agent's managed skills directory, then link or copy an individual skill folder after reviewing its prerequisites. For example:

```bash
mkdir -p "$HOME/.hermes/skills"
ln -s "$(pwd)/prompt-factory" "$HOME/.hermes/skills/prompt-factory"
```

This example expects no existing `~/.hermes/skills/prompt-factory` path. Verify that your Hermes installation discovers the skill before relying on it. The exact import and invocation method can vary by agent and version.

## Marketplace submission readiness

Agensi accepts individual `SKILL.md` skills and curated packs of up to **50 skills** per listing. **Do not upload this entire repository as one package.** The packaged ZIP is generated only from selected skill directories; root-level private documents and internal state files are excluded.

Our workflow is:

1. **Inventory** — generate [docs/SKILL_CATALOG.md](docs/SKILL_CATALOG.md) directly from file paths.
2. **Audit** — inspect every active `SKILL.md` for missing metadata, broken links, unsafe patterns, and possible secrets.
3. **Triage** — treat blocking security findings separately from warnings; investigate false positives with regression cases.
4. **Build** — package only explicitly selected, reviewed skills with deterministic ZIP output and SHA-256 checksums.
5. **Verify** — run [CI checks](.github/workflows/skill-audit.yml) and skill-specific execution tests.
6. **Release** — publish only after human review of provenance, allowed permissions, licensing, and actual results.

The library-wide audit is **static analysis**, not a guarantee of security, compatibility, legal correctness, or successful execution. See the outstanding findings in [marketplace readiness](docs/MARKETPLACE_READINESS.md).

## Contributing and quality bar

Use one directory per skill with a `SKILL.md` containing frontmatter `name` and `description`. Prefer concise prerequisites, exact procedures, a runnable verification example, known limitations, and supporting files in `references/` or `scripts/`.

Before proposing changes:

```bash
python -m unittest discover -s tests -p 'test_marketplace_*.py' -v
python tools/generate_catalog.py --check
python tools/audit_skills.py --fail-on-blockers
```

Do not commit secrets, private contracts, personal data, or generated binaries. Any high-impact change to a self-modifying skill requires a reviewed diff and regression evidence; no silent auto-merge.

## Licensing and limitations

The repository is provided under the [MIT License](LICENSE). A commercial listing must still respect any third-party components and the destination marketplace's originality requirements. Taiwan legal skills are educational and workflow-focused, **not a replacement for qualified legal review**.

---

## 繁體中文說明

**Strata Skill 是以 Hermes Agent 為主要使用情境的技能庫，目前有 142 份有效 `SKILL.md`。** 技能以提示詞工程、代理工作流程、開發維運、研究、法律文件與品質驗收為主。

- [完整技能清冊](docs/SKILL_CATALOG.md) 由程式依實際資料夾產生，不再手動填寫技能總數。
- [市場上架準備報告](docs/MARKETPLACE_READINESS.md) 會區分已完成的驗證、已知缺點與待解決事項。
- **上架 Agensi 時只挑選要販售的技能進行安全封裝**，不能直接打包整個儲存庫，也不能將自我評分當成外部品質認證。
- **閉環流程：** 發現問題 → 留存證據 → 修正 → 回歸測試 → 人工確認 → 再交付。未經驗證的功能不可標成已完成。
- 這個專案採 MIT 授權。公開技能的商業上架必須再確認第三方來源、授權及商品原創價值。

如需安裝，請先閱讀對應 `SKILL.md` 的前置條件；不同 Agent 的工具名稱與權限並不一定相同。
