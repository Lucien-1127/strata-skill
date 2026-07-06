# Deep Document → Skill Integration Pattern

How to take external research documents (articles, whitepapers, Evergreen Notes, JSON exports) and systematically weave their content into existing skills without breaking structure.

This was proven across 5 strat skills × 13 patches in a single session. Each skill grew 30-60% in content with zero structural regressions.

## Phase 0 — Inventory the Documents

Before touching any skill:

1. Map each document to the skill it enriches (not all docs go to all skills)
2. Identify the core concept from each doc (one doc = one main idea, don't over-split)
3. Read the FULL document — don't rely on summaries. The nuance lives in the details.

## Phase 1 — Read + Map the Target Skill

For each skill you're going to modify:

1. `skill_view(name)` to get current state (full SKILL.md)
2. Identify where the new concept fits:
   - New `### Phase N — {concept}` if it's a distinct step
   - Extension of an existing phase if it deepens current content
   - New `## Pitfalls` entry if it reveals a trap
3. Note the section numbering — you WILL need to renumber downstream phases

## Phase 2 — Integrate Layer by Layer

**Golden rule: add, don't replace.** Existing content works. New content extends.

### Layer 1: Core concept
Add a new `### Phase` or expand an existing one. Use tables, code blocks, and ASCII diagrams liberally — these skills are read by LLMs and humans alike.

### Layer 2: Pitfalls
Every new concept introduces new traps. Add them immediately. Format:
```
- **{Trap Name}**：{Symptom} → {Why it happens} → {Fix}
```

### Layer 3: Section renumbering
When inserting new phases, renumber ALL downstream sections. Use `patch` with a generous old_string that includes the next section's heading to ensure uniqueness.

### Layer 4: Counter-verification
After each patch, mentally run through: "Does the skill still make sense if read top-to-bottom? Does the new content contradict any existing Pitfalls?"

## Phase 3 — Cross-Reference

After all skills are updated, check:
- Does the orchestrator know about the new sub-module capabilities?
- Do sub-modules reference the orchestrator's FSM states?
- Are file paths in verification sections still correct?

## Pitfalls of the Integration Pattern

- **Don't read doc summaries only** — the reference files in `references/` are often just mapping tables. Read the actual source documents in `~/.hermes/cache/documents/` for full context.
- **Don't flatten** — a 50-line document shouldn't become a 5-line bullet list. Preserve the richness: include sample code, ASCII diagrams, and multi-column tables from the source.
- **Don't orphan pitfalls** — new concepts must come with new pitfalls. A phase without a corresponding pitfall is incomplete.
- **Don't assume skill_view reads whole file** — if the file was previously read with offset/limit, skill_view may warn. Re-read the full file before patching.
- **Section numbering is fragile** — when inserting Phase 2 before existing Phase 2, the old Phase 2 becomes Phase 3, and so on. Always update all downstream numbers in the same patch or the very next one.
