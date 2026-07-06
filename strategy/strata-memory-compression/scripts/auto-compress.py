#!/usr/bin/env python3
"""
磐石系統自動壓縮偵測器
Reads ~/.hermes/state.db to detect new/updated sessions and trigger compression.
Outputs JSON verdict for the cronjob agent to consume.
"""

import json, os, sqlite3, datetime

DB_PATH = os.path.expanduser("~/.hermes/state.db")
STATE_FILE = os.path.expanduser("~/.hermes/cron/output/auto-compress-state.json")
LOOKBACK_HOURS = 24

# Load last check state
last_check = None
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
            last_check = state.get("last_check_epoch", 0)
    except (json.JSONDecodeError, KeyError):
        last_check = 0

now_epoch = datetime.datetime.now().timestamp()

if not os.path.exists(DB_PATH):
    print(json.dumps({"error": "DB not found", "trigger": False}))
    exit(0)

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Sessions updated since last check
    since = last_check or (now_epoch - LOOKBACK_HOURS * 3600)
    c.execute("""
        SELECT id, title, started_at, ended_at, message_count, tool_call_count,
               input_tokens, output_tokens
        FROM sessions
        WHERE started_at >= ? OR (ended_at IS NOT NULL AND ended_at >= ?)
        ORDER BY started_at DESC LIMIT 10
    """, (since, since))
    sessions = [dict(r) for r in c.fetchall()]

    # Message counts
    session_ids = tuple(s["id"] for s in sessions) if sessions else ("__none__",)
    placeholders = ",".join("?" for _ in session_ids)
    c.execute(f"""
        SELECT session_id, COUNT(*) as msg_count
        FROM messages WHERE session_id IN ({placeholders})
        GROUP BY session_id
    """, session_ids)
    msg_counts = {r["session_id"]: r["msg_count"] for r in c.fetchall()}
    for s in sessions:
        s["total_messages"] = msg_counts.get(s["id"], 0)

    # Check compression_locks
    has_cl = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='compression_locks'"
    ).fetchone()
    compressed_ids = set()
    if has_cl:
        cl_placeholders = ",".join("?" for _ in session_ids)
        c.execute(f"""
            SELECT session_id FROM compression_locks
            WHERE session_id IN ({cl_placeholders})
        """, session_ids)
        compressed_ids = {r["session_id"] for r in c.fetchall()}

    conn.close()
except Exception as e:
    print(json.dumps({"error": str(e), "trigger": False}))
    exit(1)

# Decision logic
uncompressed = [
    s for s in sessions
    if s["id"] not in compressed_ids and s["total_messages"] > 3
]

trigger = bool(uncompressed) or (last_check is None and bool(sessions))
reason = ""
if not sessions:
    reason = "無新活動"
elif uncompressed:
    reason = f"發現 {len(uncompressed)} 個未壓縮 session"
elif last_check is None:
    reason = "首次執行"
else:
    hours = (now_epoch - since) / 3600
    if hours >= 12:
        reason = f"定時檢查（{hours:.0f}h）"
    else:
        reason = "無新活動"

output = {
    "trigger": trigger,
    "reason": reason,
    "since_epoch": since,
    "now_epoch": now_epoch,
    "total_sessions_found": len(sessions),
    "uncompressed_sessions": len(uncompressed),
    "sessions": sessions[:5],
    "uncompressed_ids": [s["id"] for s in uncompressed[:5]],
}

print(json.dumps(output, ensure_ascii=False, indent=2))

# Update state
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w") as f:
    json.dump({
        "last_check_epoch": now_epoch,
        "last_trigger": trigger,
        "last_reason": reason,
    }, f)
