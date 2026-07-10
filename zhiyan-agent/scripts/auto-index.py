#!/usr/bin/env python3
"""
auto-index.py — zhiyan-search 索引自動同步偵測器

檢查 zhiyan-legal docs/ 是否有 git 變更，若有則啟動 freely 代理並重建索引。
設計為 watchdog cronjob（no_agent=True）：無變更時靜默，有變更時輸出報告。

用法:
    python3 auto-index.py                    # 正常執行
    python3 auto-index.py --force            # 強制重建
    python3 auto-index.py --status           # 顯示索引狀態

相依:
    auto-index-state.json 記錄 last_indexed_commit hash
    build_index.py 執行實際向量建置
    freely.py 提供本機 embedding API
"""
import os, sys, json, time, subprocess, urllib.request
from pathlib import Path
from datetime import datetime, timezone

ZHIYAN_DIR = os.path.expanduser("/home/ysga1/zhiyan-legal")
SEARCH_DIR = os.path.expanduser("/home/ysga1/zhiyan-search")
BUILD_SCRIPT = os.path.join(SEARCH_DIR, "build_index.py")
VECTOR_STORE = os.path.join(SEARCH_DIR, "vector_store")
STATE_FILE = os.path.expanduser("~/.hermes/cron/output/auto-index-state.json")
FREELY_SCRIPT = os.path.join(SEARCH_DIR, "freely.py")
FREELY_PORT = 8008
FREELY_HEALTH = f"http://localhost:{FREELY_PORT}/health"

def get_last_indexed_commit():
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: state = json.load(f)
        except: pass
    return state.get("last_indexed_commit", "")

def save_state(commit_hash, stats=None):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    state = {"last_indexed_commit": commit_hash, "last_index_time": datetime.now(timezone.utc).isoformat()}
    if stats: state["last_stats"] = stats
    with open(STATE_FILE, "w") as f: json.dump(state, f, ensure_ascii=False, indent=2)

def get_current_head():
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%H", "--", "docs/"], capture_output=True, text=True, cwd=ZHIYAN_DIR, timeout=30)
        return r.stdout.strip()
    except: return ""

def has_docs_changed():
    last, current = get_last_indexed_commit(), get_current_head()
    if not current: return False, "無法取得 git head"
    if not last: return True, "首次索引"
    if current == last: return False, "無變更"
    try:
        r = subprocess.run(["git", "log", "--oneline", f"{last}..HEAD", "--", "docs/"], capture_output=True, text=True, cwd=ZHIYAN_DIR, timeout=30)
        count = len([l for l in r.stdout.strip().split("\n") if l.strip()]) if r.stdout.strip() else 0
        return True, f"{count} 個新 commits"
    except: return True, "無法計算"

def is_freely_running():
    try:
        req = urllib.request.Request(FREELY_HEALTH, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode()).get("status") == "ok"
    except: return False

def ensure_freely(timeout=30):
    if is_freely_running(): return True, f"freely 在線 (:{FREELY_PORT})"
    log_path = os.path.expanduser("~/.hermes/cron/output/freely.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    proc = subprocess.Popen([sys.executable, FREELY_SCRIPT], stdout=open(log_path, "a"), stderr=subprocess.STDOUT, cwd=SEARCH_DIR)
    for i in range(timeout):
        time.sleep(1)
        if is_freely_running(): return True, f"freely 就緒 ({i+1}s)"
        if proc.poll() is not None: return False, f"啟動失敗 (exit {proc.returncode})"
    return False, f"逾時 ({timeout}s)"

def get_index_stats():
    import chromadb
    try:
        c = chromadb.PersistentClient(path=VECTOR_STORE)
        return {"chunks": c.get_collection("zhiyan_docs").count(), "status": "ok"}
    except Exception as e: return {"chunks": 0, "status": f"error: {e}"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        stats = get_index_stats()
        state = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f: state = json.load(f)
        head = get_current_head()
        print(f"\n📊 zhiyan-search 索引狀態")
        print(f"{'='*40}")
        print(f"   Chunks: {stats.get('chunks', '?')}")
        print(f"   ChromaDB: {'✅ 健康' if stats.get('status') == 'ok' else '❌ ' + str(stats.get('status', '?'))}")
        print(f"   Git HEAD: {head[:16] if head else '?'}...")
        print(f"   上次索引: {state.get('last_index_time', '從未')}")
        print(f"   上次 commit: {str(state.get('last_indexed_commit', ''))[:16]}...")
        sys.exit(0)

    changed, reason = has_docs_changed()
    stats_before = get_index_stats()
    if not changed and not args.force:
        return  # watchdog silent

    print(f"🔍 {reason} | 當前: {stats_before.get('chunks', '?')} chunks")

    ok, msg = ensure_freely()
    if not ok:
        print(f"❌ {msg}")
        sys.exit(1)

    if args.force:
        hs = os.path.join(VECTOR_STORE, ".file_hashes.yaml")
        if os.path.exists(hs): os.remove(hs); print("🧹 hash store cleared")

    print(f"🏗️  建置索引...")
    log_path = os.path.expanduser("~/.hermes/cron/output/build_index.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    env = os.environ.copy(); env["PYTHONUNBUFFERED"] = "1"
    with open(log_path, "w") as log:
        log.write(f"=== {datetime.now().isoformat()} ===\n"); log.flush()
        try:
            result = subprocess.run([sys.executable, BUILD_SCRIPT], capture_output=True, text=True, cwd=SEARCH_DIR, timeout=1800, env=env)
            log.write(result.stdout)
            if result.stderr: log.write(f"\n--- STDERR ---\n{result.stderr}\n")
        except subprocess.TimeoutExpired:
            print(f"❌ 逾時 30min，日誌: {log_path}")
            sys.exit(1)

    current_head = get_current_head()
    stats_after = get_index_stats()
    save_state(current_head, {"before": stats_before.get("chunks", 0), "after": stats_after.get("chunks", 0)})

    if result.returncode == 0:
        print(f"✅ 完成: {stats_before.get('chunks',0)} → {stats_after.get('chunks',0)} chunks | commit: {current_head[:16]}...")
        for line in result.stdout.strip().split("\n")[-5:]:
            l = line.strip()
            if l and any(k in l for k in ("✅","更新","跳過","新增","總文件","Embedding")):
                print(f"   {l}")
    else:
        print(f"❌ 失敗 (exit {result.returncode})")
