#!/usr/bin/env python3
"""
save_summary_to_mem0.py — STRATA 摘要橋接腳本

讀取 MEMORY.md 的最新摘要，寫入 Mem0 Qdrant 向量庫。
支援增量跳過（已同步的摘要不重複寫入）。
設計為可被 cron job 呼叫的獨立腳本。

用法:
    python3 save_summary_to_mem0.py                    # 同步新摘要
    python3 save_summary_to_mem0.py --all              # 強制全部重新同步
    python3 save_summary_to_mem0.py --dry-run           # 僅預覽，不寫入
    python3 save_summary_to_mem0.py --status            # 顯示同步狀態
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

MEMORY_PATH = os.path.expanduser("~/.hermes/memories/MEMORY.md")
MEM0_CONFIG_PATH = os.path.expanduser("~/.hermes/mem0.json")
STATE_PATH = os.path.expanduser("~/.hermes/cron/output/mem0-sync-state.json")

_OPENAI_API_KEY_DUMMY = "sk-placeholder-for-mem0"


def create_mem0_client():
    if not os.path.exists(MEM0_CONFIG_PATH):
        print("❌ Mem0 config 不存在: " + MEM0_CONFIG_PATH)
        sys.exit(1)

    with open(MEM0_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = _OPENAI_API_KEY_DUMMY

    oss = cfg.get("oss", {})
    config = {
        "vector_store": oss.get("vector_store", {}),
        "llm": oss.get("llm", {"provider": "openai", "config": {}}),
        "embedder": oss.get("embedder", {"provider": "openai", "config": {}}),
    }

    from mem0 import Memory
    return Memory.from_config(config)


def parse_memory_entries(memory_path):
    if not os.path.exists(memory_path):
        return []

    with open(memory_path, "r", encoding="utf-8") as f:
        text = f.read()

    raw_entries = text.split("§")
    entries = []

    for i, raw in enumerate(raw_entries):
        content = raw.strip()
        if not content or len(content) < 10:
            continue

        entry_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        entry_type = classify_entry(content)

        entries.append({
            "index": i,
            "hash": entry_hash,
            "content": content,
            "raw": raw,
            "type": entry_type,
        })

    return entries


def classify_entry(content):
    if any(kw in content for kw in ["GCP VM", "GitHub:", "Email:", "Business:"]):
        return "profile"
    if content.startswith("摘要") or "摘要 " in content[:20]:
        return "summary"
    if content.startswith("決策") or "決定" in content[:30]:
        return "decision"
    if content.startswith("發現") or "發現:" in content[:30]:
        return "discovery"
    if any(kw in content for kw in ["偏好", "prefer", "不喜歡", "喜歡"]):
        return "preference"
    return "other"


def load_sync_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"synced_hashes": [], "last_sync_time": None, "total_synced": 0}


def save_sync_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def build_mem0_message(content, entry_type):
    if entry_type == "profile":
        return [
            {"role": "system", "content": "使用者資訊: " + content[:500]},
            {"role": "assistant", "content": "已記錄使用者設定檔"},
        ]
    return [{"role": "assistant", "content": content[:800]}]


def sync_to_mem0(dry_run=False, force_all=False):
    state = load_sync_state()
    synced_hashes = set(state.get("synced_hashes", []))

    entries = parse_memory_entries(MEMORY_PATH)
    print("📖 讀取到 " + str(len(entries)) + " 個條目")

    new_entries = [e for e in entries if e["hash"] not in synced_hashes or force_all]
    if not force_all:
        new_entries = [e for e in new_entries if e["type"] != "profile" or e["hash"] not in synced_hashes]

    if not new_entries:
        print("✅ 無新摘要需同步")
        return

    print("🆕 待同步: " + str(len(new_entries)) + " 個條目")
    for e in new_entries:
        preview = e["content"][:80].replace("\n", " ")
        print("   [" + e["type"] + "] " + preview)

    if dry_run:
        print("\n🏁 Dry-run 模式，未實際寫入")
        return

    m = create_mem0_client()

    success_count = 0
    for entry in new_entries:
        messages = build_mem0_message(entry["content"], entry["type"])
        try:
            result = m.add(
                messages=messages,
                user_id="太陽",
                metadata={
                    "source": "strata_summary",
                    "type": entry["type"],
                    "hash": entry["hash"],
                },
            )
            synced_hashes.add(entry["hash"])
            success_count += 1
            print("  ✅ 已寫入: " + entry["content"][:60].replace(chr(10), " ") + "...")
        except Exception as e:
            print("  ❌ 寫入失敗: " + str(e))

    state["synced_hashes"] = list(synced_hashes)
    state["last_sync_time"] = datetime.now(timezone.utc).isoformat()
    state["total_synced"] = len(synced_hashes)
    save_sync_state(state)

    print("\n" + "=" * 50)
    print("✅ 同步完成: " + str(success_count) + "/" + str(len(new_entries)) + " 條")
    print("📊 累計同步: " + str(state["total_synced"]) + " 條")


def show_status():
    state = load_sync_state()
    entries = parse_memory_entries(MEMORY_PATH)
    synced_set = set(state.get("synced_hashes", []))

    print("\n📊 Mem0 同步狀態")
    print("=" * 40)
    print("   最後同步: " + str(state.get("last_sync_time", "從未")))
    print("   已同步條目: " + str(state.get("total_synced", 0)))
    print("   MEMORY.md 條目總數: " + str(len(entries)))
    print("   待同步: " + str(len([e for e in entries if e["hash"] not in synced_set])))

    types = {}
    for e in entries:
        types[e["type"]] = types.get(e["type"], 0) + 1
    print("\n   分類:")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print("      " + t + ": " + str(c))


def main():
    parser = argparse.ArgumentParser(description="STRATA → Mem0 橋接腳本")
    parser.add_argument("--dry-run", action="store_true", help="僅預覽，不寫入")
    parser.add_argument("--all", action="store_true", help="強制全部重新同步")
    parser.add_argument("--status", action="store_true", help="顯示同步狀態")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        sync_to_mem0(dry_run=args.dry_run, force_all=args.all)


if __name__ == "__main__":
    main()
