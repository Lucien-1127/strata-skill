# Skills Directory Split — Case Study (2026-07-03)

## Symptoms
- `hermes skills list` showed only 1 skill (`zhiyan-agent`)
- `skills_list` tool returned only 1 skill
- Agent couldn't load any previously known skills via `skill_view`

## Investigation Timeline

### 1. File system check
```
ls ~/.hermes/
```
Discovered two skill directories:
- `skills/` — created 2026-07-03 21:01, contained only `zhiyan-agent`
- `skills-all/` — created 2026-07-03 17:55, contained 83 skills

### 2. Directory comparison
```
comm -23 <(ls skills-all/ | sort) <(ls skills/ | sort)
```
Output: 82 skill names missing from `skills/` that exist in `skills-all/`.

### 3. Content integrity check
Spot-checked 8 SKILL.md files — all had valid YAML frontmatter (`---`, `name:`, `description:`) and body content. Files ranged from ~10 to 233 lines.

### 4. Curator investigation
```
cat skills/.curator_state
```
Result:
```json
{
  "last_run_at": "2026-07-03T19:08:28+00:00",
  "last_run_summary": "deferred first run — curator seeded, will run after one interval",
  "run_count": 0,
  "paused": false
}
```

```
hermes curator status
```
Result: "no agent-created skills" — curator saw 0 skills.

### 5. Curator run analysis
Latest run (`logs/curator/20260703-210112/run.json`):
```json
{
  "counts": { "before": 0, "after": 0, "delta": 0 },
  "auto_transitions": { "checked": 0, "marked_stale": 0, "archived": 0 }
}
```
Curator ran but found nothing — it only scans `skills/`, not `skills-all/`.

### 6. Hub sync state
```
cat skills-all/.hub/taps.json  → {"taps": []}
cat skills-all/.hub/lock.json  → empty install list
```
No hub-installed skills tracked.

### 7. Config check
```
grep -i "skill" config.yaml
```
No `skills.path` override — system uses default `skills/` directory.

## Root Cause
Skill directories diverged: `skills-all/` (17:55, 83 skills) was replaced by `skills/` (21:01, 1 skill) during curator initialization or profile reset. Active Hermes reads from `skills/`, which was nearly empty.

## Recovery
Copy all skills from `skills-all/` back to `skills/`:
```
comm -23 <(ls skills-all/ | sort) <(ls skills/ | sort) | while read name; do
    cp -r "skills-all/$name" "skills/$name"
done
```

## Key Diagnostic Commands Used
```bash
stat -c '%y %n' skills skills-all
comm -23 <(ls skills-all/|sort) <(ls skills/|sort)
cat skills/.curator_state
hermes curator status
grep -i "skill" config.yaml
cat skills-all/.hub/taps.json
read_file logs/curator/<latest>/run.json
```