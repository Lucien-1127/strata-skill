# Post-Setup Project Verification — zhiyan-legal (2026-07-04)

**Context:** After confirming VM services, the project was verified by running the test suite.
Result: **123 tests → 122 passed, 1 failed.** The single failure was a version reference mismatch.

## The Bug

### Symptom
```
tests/test_manifest.py::TestDocsDir::test_task_layer_files_exist FAILED
AssertionError: 以下 TASK_LAYERS 檔案不存在：
  TA/40_模組與人格層/51_人格_助教批改_v1.1.0.md
```

### Root Cause
`src/zhiyan_legal/manifest.py` referenced `51_人格_助教批改_v1.1.0.md`, but the actual file on disk had been bumped to `v1.2.0.md`.

```python
# Line 63 in manifest.py — BEFORE
Layer("TA Persona", "40_模組與人格層", ["51_人格_助教批改_v1.1.0.md"]),

# AFTER fix
Layer("TA Persona", "40_模組與人格層", ["51_人格_助教批改_v1.2.0.md"]),
```

### Why It Happened
The doc file got updated (version bump in filename) but the manifest was never updated to match. This is a common maintenance gap in doc-heavy projects where filenames encode version numbers.

### Fix Verification
After patching `manifest.py`, re-running the full suite:
```
123 passed in 1.03s
```

## Additional Git Hygiene

- `data/zhiyan.db` was showing as untracked
- Added `data/zhiyan.db` to `.gitignore` under the `# Data artifacts` section
- Then staged the `.gitignore` change

## Takeaway Pattern

When a test fails because a referenced file doesn't exist:

1. **Read the failure path** — it tells you exactly what was expected
2. **Check what's actually on disk** — `ls` the directory the file should be in
3. **Search for the old reference** — `grep -rn "old_filename_version" src/ tests/`
4. **Fix the reference** — it's usually a one-line change in a manifest/config file
5. **Re-run** — confirm the fix works

This pattern repeats whenever docs get version bumps without manifest updates.
