# GitHub SSH vs REST API Gap — Worked Example

## Session Context

Date: 2026-07-10
Task: Update profile README (Lucien-1127/Lucien-1127) and set repo topics
Environment: GCP VM, Hermes Agent session with `deepseek-chat`

## What Worked (SSH git)

```bash
# SSH authentication to GitHub
ssh -T git@github.com
# Output: Hi Lucien-1127! You've successfully authenticated...

# Clone, commit, push — all via SSH
git clone git@github.com:Lucien-1127/Lucien-1127.git
git add README.md
git commit -m "enhance: update profile README ..."
git push origin main
# Output: To github.com:Lucien-1127/Lucien-1127.git
#          588b361..b9e7376  main -> main
```

## What Failed (REST API — needs token)

```bash
# Direct API call — 401
curl -s -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $(cat ~/.config/gh/hosts.yml 2>/dev/null | grep oauth_token | head -1 | awk '{print $2}')" \
  https://api.github.com/repos/Lucien-1127/Lucien-1127/topics \
  -d '{"names":["ai","legal-tech","taiwan","hermes-agent","prompt-engineering","llm"]}'
# Output: {"message":"Bad credentials","status":"401"}
```

## Tried but Failed

| Approach | Result | Root cause |
|----------|--------|------------|
| `gh CLI` via `apt` | Installed but `gh auth login` requires device flow + browser | No TTY, no browser |
| `gh` binary download | Same — device flow only | Interactive step unavoidable |
| `PyGithub` library | Needs token | No token available |
| SSH key in `ssh-agent` | Doesn't work for REST API | GitHub API doesn't accept SSH auth |
| OAuth device flow | Generated code but needs browser visit | Requires user action |
| Browser sign-in | Reached login page but no credentials stored | Can't auto-fill |
| `GITHUB_TOKEN` env var | Not set | Not configured in env or dotfiles |

## The Core Pattern

1. **SSH key** → `git@github.com:user/repo.git` → git push/pull ✅
2. **No token** → `api.github.com` → all REST endpoints fail ❌
3. **Solution** requires user action: either provide a PAT or complete the device flow

## Key Takeaway

When you see "Hi username! You've successfully authenticated" from `ssh -T git@github.com`, that confirms SSH git access only. Do not assume REST API access works. Test separately.

The desired topics for this repo were:
`ai, legal-tech, taiwan, hermes-agent, prompt-engineering, llm`

These were not set due to the credential gap. The fallback was to commit the README update via SSH git (which worked) and inform the user about the topics gap.
