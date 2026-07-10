---
name: github-repo-metadata-batch
description: Batch-update GitHub repo metadata (description, topics) across multiple repos via GitHub API — inventory, prepare gh CLI, execute, verify.
version: 0.1.0
author: Hermes
platforms: [linux]
tags:
  - GitHub
  - Batch
  - Metadata
  - API
  - Topics
  - Description
status: stable
---

# GitHub Repo Metadata Batch Updater

Batch-update descriptions and topics (GitHub tags) across a fleet of repos. Covers inventory of current state, authentication diagnostics, `gh` CLI setup without root, and verification.

## When to Use

- User says "幫所有 repo 補上 topics 與 description" / "update descriptions and topics"
- User provides a list of repos needing metadata updates
- After creating new repos that need initial descriptions and topics
- Cleanup sweep — standardizing repo descriptions with consistent formatting

## Prerequisites

- GitHub repos exist (public or private you have write access to)
- Some form of GitHub authentication available:
  - **Preferred**: `GH_TOKEN` or `GITHUB_TOKEN` environment variable
  - **Alternative**: `gh` CLI authenticated (`gh auth status`)
  - **Minimal read-only**: unauthenticated API (60 req/hr limit) — can inventory but cannot write

## Procedure

### Phase 1 — Inventory Current State

Query each repo's current description and topics via the unauthenticated API (works for public repos):

```bash
curl -s "https://api.github.com/repos/<owner>/<repo>" -o /tmp/<repo>.json
python3 -c "
import json
d = json.load(open('/tmp/<repo>.json'))
print('desc:', d.get('description'))
print('topics:', d.get('topics'))
"
```

Batch inventory all repos at once:

```bash
for repo in repo1 repo2 repo3; do
  curl -s "https://api.github.com/repos/<owner>/$repo" -o "/tmp/$repo.json" \
    && python3 -c "import json; d=json.load(open('/tmp/$repo.json')); print(f'$repo: desc={d.get(\"description\")!r}, topics={d.get(\"topics\")}')"
done
```

### Phase 2 — Authentication Diagnostics

Check if write auth is available; the GitHub API returns `401` on unauthenticated PATCH:

```bash
# Test: is gh CLI available?
which gh 2>/dev/null || echo "gh not installed"

# Test: is gh authenticated?
gh auth status 2>&1

# Test: are token env vars set?
echo "${GH_TOKEN:+GH_TOKEN is set}"
echo "${GITHUB_TOKEN:+GITHUB_TOKEN is set}"

# Test: can we do a PATCH (expect 401 without auth)?
curl -s -o /dev/null -w "%{http_code}" -X PATCH \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<owner>/<repo>" \
  -d '{"description":"test"}'
```

Result matrix:

| Signal | Meaning | Action |
|--------|---------|--------|
| `gh` not installed | No CLI available | Install via binary download (see below) |
| `gh auth status` OK | CLI is ready | Use `gh repo edit` (Phase 4) |
| `GH_TOKEN` is set | Token available | Set `GH_TOKEN`, use `gh` or `curl` |
| PATCH returns `200` | Unauthenticated write? | Unlikely — only happens for rare edge cases |
| PATCH returns `401` | Need authentication | Go to Phase 3 |

#### Install `gh` CLI Without Root

```bash
cd /tmp
curl -sL "https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz" -o gh.tar.gz
tar xzf gh.tar.gz
cp gh_2.67.0_linux_amd64/bin/gh /tmp/gh
/tmp/gh --version
# Can invoke as /tmp/gh for the rest of the session
# Or add to PATH: export PATH="/tmp:$PATH"
```

### Phase 3 — Provide/Request GitHub PAT

If no token is found, the user must provide a **GitHub PAT** (classic or fine-grained) with `repo` scope (or `public_repo` for public repos). Set it:

```bash
export GH_TOKEN="<token>"
# Then verify:
gh repo view <owner>/<repo> 2>&1 | head -5
```

Pitfall: SSH keys (`ssh -T git@github.com`) authenticate for **git operations** (clone/push/pull) but NOT for **GitHub API write operations** (PATCH repos, update topics). A PAT is required for API write access.

### Phase 4 — Execute Updates

Using `gh` CLI:

```bash
# Set a new description
gh repo edit <owner>/<repo> --description "<new description>"

# Add topics (one --add-topic flag per topic)
gh repo edit <owner>/<repo> \
  --add-topic topic1 \
  --add-topic topic2 \
  --add-topic topic3

# Remove a topic
gh repo edit <owner>/<repo> --remove-topic topic-name

# Set topics entirely (replaces all):
gh repo edit <owner>/<repo> --add-topic topic1 --add-topic topic2
```

**Important**: `--add-topic` is **additive** — it adds to existing topics. Topics already set are preserved. There is no `--set-topics` flag; to replace all topics, you need to first remove then add, or use the API directly:

```bash
curl -s -X PATCH "https://api.github.com/repos/<owner>/<repo>" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"topics":["topic1","topic2","topic3"], "description":"My description"}'
```

Batch script pattern:

```bash
#!/bin/bash
GH=/tmp/gh
OWNER="your-org-or-user"

# Each repo: description + topics
repos=(
  "repo1:Description one:topic-a,topic-b"
  "repo2:Description two:topic-c,topic-d"
)

for entry in "${repos[@]}"; do
  IFS=':' read -r name desc topics_str <<< "$entry"
  IFS=',' read -ra topics <<< "$topics_str"
  echo "=== Updating $name ==="
  $GH repo edit "$OWNER/$name" --description "$desc"
  for topic in "${topics[@]}"; do
    $GH repo edit "$OWNER/$name" --add-topic "$topic"
  done
done
```

Using `curl` directly (no `gh` dependency):

```bash
curl -s -X PATCH "https://api.github.com/repos/$OWNER/$REPO" \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -H "Content-Type: application/json" \
  -d "$(cat <<EOF
{
  "description": "$DESCRIPTION",
  "topics": ["topic1", "topic2"]
}
EOF
)"
```

**Note**: The `application/vnd.github.mercy-preview+json` accept header enables the `topics` field in API responses. The write API uses `application/vnd.github+json` which also supports topics.

### Phase 5 — Verification

Verify each repo's updated metadata:

```bash
for repo in repo1 repo2 repo3; do
  curl -s "https://api.github.com/repos/$OWNER/$repo" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'$repo: desc={d.get(\"description\")!r}, topics={d.get(\"topics\")}')"
done
```

Or via `gh`:

```bash
gh repo view <owner>/<repo> --json description,repositoryTopics
```

## Description Style Guidelines

For user's repos (Lucien-1127):

- **Language**: Traditional Chinese (Taiwan) — concise and punchy
- **Format**: `<category> — <key feature phrase>` using em-dash (—)
- **Length**: 20–50 characters
- **Examples**:  
  - `AI 動畫影片自動化管線 — Agnes AI + Frame Chaining + 角色一致性`
  - `Hermes Agent 技能庫 — 提示詞工程、自動化、DevOps、法律 AI`
  - `智研 AI 法律系統 — 台灣法律 AI 研究助手（PWA + FastAPI）`

## Pitfalls

- **No PAT = no write**: SSH key auth works for `git push/pull` but NOT for GitHub API metadata operations. The `gh` CLI also requires a PAT or OAuth token for API calls. Always check this early.
- **`gh` binary download path**: If installed to `/tmp/gh`, that path only lives for the current session. Use the full path or copy to a permanent location (`~/.local/bin/gh`).
- **`--add-topic` is additive**: Topics accumulate. If you need to replace all topics, you must first remove undesired ones with `--remove-topic`, or use the `curl` approach with a full `topics` array.
- **Rate limits**: Unauthenticated API is capped at 60 requests/hour. For 9+ repos, this is fine for a single inventory pass. For write operations with a token, the limit is 5,000/hour.
- **Description is null by default**: New/empty repos show `"description": null`, not an empty string. Check for `None` in Python output.
- **Topics API preview**: The `topics` field requires the `mercy-preview` media type for read operations. Write operations work with standard `vnd.github+json`.
- **`gh repo edit` supports only one `--add-topic` per call**: You can chain multiple calls or pass multiple flags. In practice, passing them one at a time works but is slow — prefer a single `curl` PATCH with the full topics array for efficiency.

## Verification

One-shot confirmation across all repos:

```bash
for repo in repo1 repo2 repo3; do
  curl -s "https://api.github.com/repos/$OWNER/$repo" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); desc=d.get('description'); topics=d.get('topics'); print(f'OK {desc!r} [{len(topics)} topics]' if desc and topics else f'? desc={\"set\" if desc else \"MISSING\"} topics={\"set\" if topics else \"MISSING\"}')"
done
```
