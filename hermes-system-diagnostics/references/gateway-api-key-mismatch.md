# Gateway API Key Not Found — Case Study (2026-07-06)

## Symptoms
- Gateway returns: `RuntimeError: Provider 'deepseek' is set in config.yaml but no API key was found`
- User sees "Sorry, I encountered an unexpected error" when trying to chat
- Error appears in `~/.hermes/logs/errors.log` with full traceback
- But `echo $DEEPSEEK_API_KEY` in the user's shell shows the key is set

## Investigation Timeline

### 1. Check gateway process environment
```bash
cat /proc/$(pgrep -f "gateway" | head -1)/environ | tr '\0' '\n' | grep -i "deepseek\|API_KEY"
```
Result: No DEEPSEEK_API_KEY in gateway's environment.

### 2. Check current shell environment
```bash
echo "DEEPSEEK_API_KEY set: $([ -n "$DEEPSEEK_API_KEY" ] && echo 'YES (length: '${#DEEPSEEK_API_KEY}')' || echo 'NO')"
```
Result: YES — the key exists in the current shell session.

### 3. Check Hermes .env file
```bash
cat ~/.hermes/.env | grep -i DEEPSEEK
```
Result: Empty — no DEEPSEEK_API_KEY in `.env`.

## Root Cause
The user set `DEEPSEEK_API_KEY` in their shell rc file (`~/.bashrc` or similar), but the **Gateway process reads environment variables from `~/.hermes/.env`**, not from the user's shell environment. The shell rc file is only sourced for interactive login shells — the gateway is a systemd-managed or supervisor-managed process that doesn't inherit those.

The config redactor issue (previous bug where the API key was truncated when stored in `config.yaml`) was already fixed by moving it to an environment variable, but that fix only applied to the **interactive shell**, not to the Gateway process.

## Fix
1. Append to `.env`:
```bash
echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY" >> ~/.hermes/.env
```

2. Restart the Gateway process:
```bash
pkill -f "hermes.*gateway"
# Gateway will auto-restart if managed by systemd/supervisor
# Otherwise restart manually
```

3. Verify the fix by checking the error log or simply testing a chat.

## Key Diagnostic Commands
```bash
# Check if key is in .env
grep DEEPSEEK ~/.hermes/.env

# Check gateway process env
cat /proc/$(pgrep -f "gateway" | head -1)/environ | tr '\0' '\n' | grep DEEPSEEK

# Check hermes .env content
cat ~/.hermes/.env

# Recent errors
tail -50 ~/.hermes/logs/errors.log
```

## Prevention
**Always add provider API keys to `~/.hermes/.env`**, not just to the user's shell rc file. The `.env` file is the canonical place for Hermes Gateway secrets. Verify by restarting the gateway and checking its process environment.
