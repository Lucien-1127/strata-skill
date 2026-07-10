---
name: obsidian-vault-maintenance
description: "Comprehensive Obsidian vault maintenance covering plugin diagnostics, configuration cleanup, frontmatter repair, and vau"
status: stable
---
# obsidian-vault-maintenance

## 📖 Description

Comprehensive Obsidian vault maintenance covering plugin diagnostics, configuration cleanup, frontmatter repair, and vault health checks.

---

# Obsidian Vault Maintenance

Diagnose, clean, and maintain Obsidian vaults. Covers plugin management, configuration hygiene, frontmatter repair, and vault organization.

## 1. Plugin Diagnostics Workflow

When diagnosing plugin issues or cleanup needs:

1. List `community-plugins.json` — read `vault/.obsidian/community-plugins.json`
2. List installed plugin folders — read `vault/.obsidian/plugins/` directory
3. Compare — find plugins installed but NOT enabled, and vice versa
4. Check manifests — read each plugin's `manifest.json` for version/authors
5. Inspect data.json files — look for bloated configs, empty settings, stale references
6. Check workspace.json — look for stale file references (deleted notes still open)
7. Check inbox/captures — look for double frontmatter, garbage content, unprocessed captures

### Pitfall: Installed-but-not-enabled plugins
Plugins in `.obsidian/plugins/` that are NOT in `community-plugins.json` are dead weight. They slow down startup, may cause errors, and waste disk space.
- Fix: Move to backup directory (do not delete until confirmed safe)

### Pitfall: Double frontmatter in captured notes
When QuickAdd captures content that already has YAML frontmatter, two `---` blocks appear. This breaks Dataview, Linter, and other metadata-aware plugins.
- Detection: Count occurrences of `---` at start of lines in `.md` files
- Fix: Merge into single frontmatter, preserving all unique fields

### Pitfall: Workspace references to deleted files
When files are deleted manually (not through Obsidian), `workspace.json` retains stale references causing errors on startup.
- Detection: Scan workspace.json for `file` keys pointing to non-existent paths
- Fix: Remove stale entries from workspace

## 2. Copilot Plugin Cleanup

The Copilot plugin bloats with unused model/provider entries (30+ models common).

### Diagnostic:
- Read data.json
- Count activeModels (often 30+)
- Identify which are actually enabled (enabled: true)
- Check if API keys are empty for unused providers

### Cleanup Strategy:
1. Keep only enabled models — filter activeModels to only enabled: true entries
2. Remove unused providers — delete entries for providers you never use (OpenAI, Anthropic, Google, OpenRouter, xAI, SiliconFlow, Cohere, Azure)
3. Clear API keys — set all apiKey fields to "" for unused providers
4. Keep essential fields — preserve userId, defaultModelKey, embeddingModelKey, system prompts
5. Backup first — always copy data.json before modifying

### Typical minimal model set for custom provider users:
- Keep only the models that use your configured custom provider
- Remove all built-in provider entries (openai, anthropic, google, openrouterai, etc.)
- Reduce activeEmbeddingModels similarly

## 3. Configuration Hygiene Checklist

For each plugin's data.json:

- Dataview: date formats, refresh interval, HTML rendering
- Templater: folder template paths exist, shell path correct
- QuickAdd: capture paths exist, templates exist
- Linter: enabled rules actually needed, YAML formatting
- Omnisearch: index settings, excluded folders
- Metadata Menu: empty presetFields, unused fileClassQueries
- Obsidian Git: auto-sync settings, commit messages
- Homepage: startup note exists
- Tasks: global query, date formats
- Tag Wrangler: usually empty, verify no conflicts
- Style Settings: usually empty, verify no conflicts

## 4. Backup Convention

All backups go to: `<vault>/.obsidian/plugins-backup/YYYYMMDD-HHMMSS/`

Structure:
```
plugins-backup/
  YYYYMMDD-HHMMSS/
    copilot-data.json.bak
    note-refactor-obsidian.removed/
    obsidian-kanban.removed/
    obsidian-various-complements-plugin.removed/
```

## 5. Verification Steps

After any maintenance:
1. Verify `community-plugins.json` matches enabled plugins
2. Verify all referenced file paths exist in vault
3. Run a sample Dataview query to confirm metadata parsing works
4. Check that no double frontmatter remains in inbox notes
5. Confirm workspace.json has no references to deleted files

## 6. Related Skills

- `obsidian-prompt-batch-optimizer` — For batch optimizing prompt files within a vault
- `legal-db-ai-fill` — For batch AI-filling spreadsheet cells related to legal databases

## 7. Diagnostic Script

- `scripts/diagnose_copilot.py` — Counts models/providers in Copilot data.json, identifies empty API keys, groups by provider, recommends cleanup. Usage: `python scripts/diagnose_copilot.py <vault_path>`