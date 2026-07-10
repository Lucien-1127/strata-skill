#!/usr/bin/env python3
"""
pipeline-feg.py — Media Pipeline v3.0 FEG + State Machine + Hooks

Finite Execution Graph:
  S0 Script → Pre-flight Hook → [per scene: IMAGE_GEN → IMAGE_DONE Hook → VIDEO_GEN → POLLING → VIDEO_DONE Hook → DOWNLOAD → COMPLETE] → Pre-concat Hook → CONCAT → Post-completion Hook → Deliver

每場景獨立 State Machine，支援 retry/skip/自我修正。
"""
import os, sys, json, time, argparse, subprocess, uuid, re
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Configuration ──
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
ENV_PATH = os.path.expanduser("~/.hermes/env/agnes.env")
SKILL_DIR = BASE_DIR.parent

# Agnes API
HEADERS = {}
AGNES_BASE = "https://apihub.agnes-ai.com"
AGNES_API = f"{AGNES_BASE}/v1"

# ── State Machine ──
STATE_IDLE = "IDLE"
STATE_QUEUED = "QUEUED"
STATE_IMAGE_GEN = "IMAGE_GEN"
STATE_IMAGE_DONE = "IMAGE_DONE"
STATE_RETRY_IMAGE = "RETRY_IMAGE"
STATE_VIDEO_GEN = "VIDEO_GEN"
STATE_POLLING = "POLLING"
STATE_VIDEO_DONE = "VIDEO_DONE"
STATE_RETRY_VIDEO = "RETRY_VIDEO"
STATE_DOWNLOADING = "DOWNLOADING"
STATE_COMPLETE = "COMPLETE"
STATE_SKIPPED = "SKIPPED"
STATE_FAILED = "FAILED"

STATE_TRANSITIONS = {
    STATE_IDLE: [STATE_QUEUED],
    STATE_QUEUED: [STATE_IMAGE_GEN],
    STATE_IMAGE_GEN: [STATE_IMAGE_DONE, STATE_RETRY_IMAGE, STATE_SKIPPED],
    STATE_IMAGE_DONE: [STATE_VIDEO_GEN],
    STATE_VIDEO_GEN: [STATE_POLLING],
    STATE_POLLING: [STATE_VIDEO_DONE, STATE_RETRY_VIDEO, STATE_SKIPPED],
    STATE_VIDEO_DONE: [STATE_DOWNLOADING],
    STATE_DOWNLOADING: [STATE_COMPLETE, STATE_RETRY_VIDEO],
    STATE_RETRY_IMAGE: [STATE_IMAGE_GEN, STATE_SKIPPED],
    STATE_RETRY_VIDEO: [STATE_VIDEO_GEN, STATE_SKIPPED],
}

# ── Default Scenes ──
DEFAULT_SCENES = [
    {"title": "開場 — 舞台聚光燈", "prompt": "Anime idol girl on stage under spotlight, pastel pink twintails, sparkling costume, cinematic angle, high detail"},
    {"title": "主歌 — 深情歌唱", "prompt": "Close-up of anime idol singing into microphone, blue eyes sparkling, gentle smile, soft bokeh background"},
    {"title": "副歌 — 舞蹈動作", "prompt": "Dynamic mid-shot of anime idol dancing on stage, colorful stage lights, sparkle particles, energetic pose"},
    {"title": "尾聲 — 綻放笑容", "prompt": "Wide shot of anime idol waving to audience, confetti falling, huge smile, warm golden lighting"},
]


# ═══════════════════════════════════════════
#  HOOK: Pre-flight (State Machine初始化前執行)
# ═══════════════════════════════════════════
def hook_preflight() -> list[str]:
    """Return list of warnings; empty = all clear."""
    warnings = []

    # 1. Agnes key
    global HEADERS
    key = ""
    if os.path.isfile(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                m = re.match(r'^\s*AGNES_API_KEY=(.*)$', line.strip())
                if m:
                    key = m.group(1).strip('"\'')
    if not key:
        # Try symlink auto-fix
        agnes_envs = list(Path(os.path.expanduser("~/.hermes/env")).glob("agnes-*.env"))
        if agnes_envs:
            src = str(agnes_envs[0])
            os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
            if os.path.islink(ENV_PATH) or os.path.isfile(ENV_PATH):
                os.remove(ENV_PATH)
            os.symlink(src, ENV_PATH)
            warnings.append(f"🔧 Auto-fix: symlinked {os.path.basename(src)} → agnes.env")
            with open(ENV_PATH) as f:
                for line in f:
                    m = re.match(r'^\s*AGNES_API_KEY=(.*)$', line.strip())
                    if m:
                        key = m.group(1).strip('"\'')
        if not key:
            warnings.append("❌ AGNES_API_KEY not found. Create ~/.hermes/env/agnes.env")
            return warnings

    HEADERS = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    warnings.append(f"✅ Agnes key loaded ({key[:8]}...{key[-4:]})")

    # 2. httpx
    try:
        import httpx
        warnings.append("✅ httpx available")
    except ImportError:
        warnings.append("❌ httpx not installed. Run: pip install httpx")
        return warnings

    # 3. ffmpeg
    ffmpeg_check = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
    if ffmpeg_check.returncode == 0:
        warnings.append(f"✅ ffmpeg found: {ffmpeg_check.stdout.strip()}")
    else:
        warnings.append("⚠️ ffmpeg not found—CONCAT mode will fail")

    # 4. Disk space
    try:
        st = os.statvfs(str(OUTPUT_DIR)) if OUTPUT_DIR.exists() else os.statvfs("/")
        free_gb = (st.f_frsize * st.f_bavail) / (1024**3)
        if free_gb < 0.5:
            warnings.append(f"⚠️ Low disk space: {free_gb:.1f}GB free (< 0.5GB)")
        else:
            warnings.append(f"✅ Disk: {free_gb:.1f}GB free")
    except:
        warnings.append("⚠️ Could not check disk space")

    return warnings


# ═══════════════════════════════════════════
#  STATE: IMAGE_GEN
# ═══════════════════════════════════════════
def state_image_gen(scene: dict, scene_idx: int) -> tuple[str, Optional[str]]:
    """Returns (next_state, image_url_or_None)"""
    import httpx
    print(f"\n🎨 [{scene['title']}] 文生圖...")
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": scene["prompt"],
        "size": "768x1152",
        "n": 1,
    }
    try:
        r = httpx.post(f"{AGNES_API}/images/generations",
                       headers=HEADERS, json=payload, timeout=120)
        data = r.json()
        img_url = data.get("data", [{}])[0].get("url", "")
        if not img_url:
            print(f"  ⚠️ 無圖片 URL: {str(data)[:200]}")
            return STATE_RETRY_IMAGE, None
        print(f"  ✅ 圖片完成")
        return STATE_IMAGE_DONE, img_url
    except Exception as e:
        print(f"  ⚠️ 例外: {e}")
        return STATE_RETRY_IMAGE, None


# ═══════════════════════════════════════════
#  HOOK: Post-Image
# ═══════════════════════════════════════════
def hook_post_image(img_url: str) -> bool:
    """Validate image URL. Return True if valid."""
    if not img_url:
        print("  ❌ Hook: 圖片 URL 為空")
        return False
    if not img_url.startswith("https://"):
        print(f"  ⚠️ Hook: 圖片 URL 非 HTTPS: {img_url[:50]}")
        return False
    return True


# ═══════════════════════════════════════════
#  STATE: VIDEO_GEN → POLLING
# ═══════════════════════════════════════════
def state_video_gen(image_url: str, scene: dict, scene_idx: int, duration: int) -> tuple[str, Optional[str]]:
    """Returns (next_state, video_id_or_None)"""
    import httpx

    fps = 24
    num_frames = duration * fps
    num_frames = ((num_frames - 1) // 8) * 8 + 1
    num_frames = min(num_frames, 441)

    print(f"\n🎬 [{scene['title']}] 建立任務 ({num_frames}幀 ~{num_frames//fps}秒)...")
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": scene["prompt"],
        "image": image_url,
        "num_frames": num_frames,
        "frame_rate": fps,
    }
    try:
        r = httpx.post(f"{AGNES_API}/videos",
                       headers=HEADERS, json=payload, timeout=60)
        data = r.json()
        task_id = data.get("task_id", "")
        video_id = data.get("video_id", "")
        if not task_id:
            print(f"  ⚠️ 任務建立失敗: {str(data)[:200]}")
            return STATE_RETRY_VIDEO, None
        print(f"  ✅ 任務已建立: video_id={video_id[:40]}...")
        return state_polling(video_id, scene, scene_idx)
    except Exception as e:
        print(f"  ⚠️ 例外: {e}")
        return STATE_RETRY_VIDEO, None


def state_polling(video_id: str, scene: dict, scene_idx: int, timeout: int = 600) -> tuple[str, Optional[str]]:
    """Returns (next_state, video_url_or_None)"""
    import httpx
    print(f"  ⏳ 渲染中...", end="", flush=True)
    deadline = time.time() + timeout
    last_progress = 0
    while time.time() < deadline:
        try:
            r = httpx.get(f"{AGNES_BASE}/agnesapi",
                          params={"video_id": video_id, "model_name": "agnes-video-v2.0"},
                          headers=HEADERS, timeout=30)
            data = r.json()
            status = data.get("status", "unknown")
            elapsed = int(time.time() - last_progress - 10) if last_progress else 0

            if status == "completed":
                video_url = data.get("url", "") or data.get("remixed_from_video_id", "")
                if video_url:
                    print(f"\n  ✅ 渲染完成!")
                    return STATE_VIDEO_DONE, video_url
                else:
                    print(f"\n  ⚠️ completed 但無 URL")
                    return STATE_RETRY_VIDEO, None
            elif status in ("failed", "error"):
                err = data.get("error", "unknown")
                print(f"\n  ❌ 失敗: {err}")
                return STATE_RETRY_VIDEO, None
            else:
                # Progress dot
                if elapsed > 0:
                    print(".", end="", flush=True)
                last_progress = time.time()
            time.sleep(10)
        except httpx.TimeoutException:
            print("T", end="", flush=True)
            continue
        except Exception as e:
            print(f"\n  ⚠️ 輪詢例外: {e}")
            return STATE_RETRY_VIDEO, None

    print(f"\n  ⏰ 輪詢超時 ({timeout}s)")
    return STATE_RETRY_VIDEO, None


# ═══════════════════════════════════════════
#  HOOK: Post-Video
# ═══════════════════════════════════════════
def hook_post_video(video_url: str) -> bool:
    """Validate video URL."""
    if not video_url:
        return False
    if not video_url.startswith("https://"):
        return False
    return True


# ═══════════════════════════════════════════
#  STATE: DOWNLOADING
# ═══════════════════════════════════════════
def state_download(video_url: str, scene_idx: int, run_id: str) -> tuple[str, Optional[Path]]:
    """Returns (next_state, output_path_or_None)"""
    import httpx
    print(f"  📥 下載影片...")
    out_path = OUTPUT_DIR / f"scene_{scene_idx+1:02d}_{run_id}.mp4"
    try:
        r = httpx.get(video_url, timeout=120)
        if r.status_code != 200:
            print(f"  ❌ HTTP {r.status_code}")
            return STATE_RETRY_VIDEO, None
        out_path.write_bytes(r.content)
        size = out_path.stat().st_size
        if size == 0:
            print(f"  ❌ 空檔案")
            out_path.unlink(missing_ok=True)
            return STATE_RETRY_VIDEO, None
        print(f"  ✅ 已儲存 ({size/1024/1024:.1f}MB)")
        return STATE_COMPLETE, out_path
    except Exception as e:
        print(f"  ⚠️ 下載例外: {e}")
        return STATE_RETRY_VIDEO, None


# ═══════════════════════════════════════════
#  HOOK: Pre-concat
# ═══════════════════════════════════════════
def hook_pre_concat(video_files: list, skipped: list) -> str:
    """Returns action: 'concat', 'single', or 'abort'"""
    n = len(video_files)
    print(f"\n  🔗 Pre-concat Hook: {n} 場景成功, {len(skipped)} 跳過")
    if skipped:
        print(f"  ⚠️  跳過場景: {skipped}")
    if n >= 2:
        return "concat"
    elif n == 1:
        return "single"
    return "abort"


# ═══════════════════════════════════════════
#  STATE: CONCAT
# ═══════════════════════════════════════════
def state_concat(video_files: list[Path], run_id: str) -> Optional[Path]:
    """ffmpeg concat → final_{run_id}.mp4"""
    print(f"\n🔗 串接 {len(video_files)} 場景...")
    filelist = OUTPUT_DIR / f"concat_list_{run_id}.txt"
    filelist.write_text("\n".join(f"file '{f.name}'" for f in video_files))
    final_path = OUTPUT_DIR / f"final_{run_id}.mp4"

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(final_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  ❌ ffmpeg: {result.stderr[-200:]}")
        return None
    size = final_path.stat().st_size
    print(f"  ✅ 最終影片: {final_path.name} ({size/1024/1024:.1f}MB)")
    return final_path


# ═══════════════════════════════════════════
#  HOOK: Post-completion（自我修正）
# ═══════════════════════════════════════════
def hook_post_completion(stats: dict, run_id: str):
    """記錄統計、清理暫存、自我修正"""
    print(f"\n{'='*50}")
    print(f"📊 流水線完成 (run_id={run_id})")
    print(f"   總場景: {stats['total']}")
    print(f"   成功: {stats['success']}")
    print(f"   跳過: {stats['skipped']}")
    print(f"   失敗: {stats['failed']}")
    print(f"   總時長: ~{stats['total_duration']}秒")

    # Save execution report
    report = OUTPUT_DIR / f"pipeline_{run_id}.json"
    stats["run_id"] = run_id
    stats["finished_at"] = datetime.now().isoformat()
    report.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"   報告: {report.name}")

    # Self-correction: if errors found, note for SKILL.md update
    if stats["failed"] > 0 or stats["skipped"] > 0:
        print(f"\n⚠️ 偵測到 {stats['failed']+stats['skipped']} 個錯誤 — 建議更新 SKILL.md Pitfalls")
        error_summary = OUTPUT_DIR / f"error_summary_{run_id}.json"
        error_summary.write_text(json.dumps(stats.get("errors", []), ensure_ascii=False, indent=2))
        print(f"   錯誤摘要: {error_summary.name}")
    print(f"{'='*50}")


# ═══════════════════════════════════════════
#  FEG Main Loop
# ═══════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Media Pipeline v3.0 — FEG + State Machine + Hooks")
    parser.add_argument("--topic", type=str, default="", help="主題描述")
    parser.add_argument("--scenes", type=int, default=4, help="場景數 (1-10)")
    parser.add_argument("--duration", type=int, default=5, help="每場景秒數 (1-18)")
    parser.add_argument("--scenes-file", type=str, default="", help="自訂場景 JSON")
    parser.add_argument("--max-retries", type=int, default=3, help="每場景最大重試次數")
    parser.add_argument("--poll-timeout", type=int, default=600, help="輪詢超時秒數")
    parser.add_argument("--output-dir", type=str, default="", help="輸出目錄")
    parser.add_argument("--skip-user-confirm", action="store_true", help="跳過使用者確認（全自動）")
    args = parser.parse_args()

    global OUTPUT_DIR
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_id = str(uuid.uuid4())[:8]

    # ── FEG Step 0: 腳本載入 ──
    if args.scenes_file and os.path.isfile(args.scenes_file):
        with open(args.scenes_file) as f:
            scenes = json.load(f)
    else:
        scenes = DEFAULT_SCENES
    scene_count = min(args.scenes, len(scenes))
    if scene_count == 0:
        print("❌ 無場景可執行")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"🎬 FEG Media Pipeline v3.0 (run_id={run_id})")
    print(f"   主題: {args.topic or '預設'}")
    print(f"   場景: {scene_count} × {args.duration}秒")
    print(f"   重試: {args.max_retries}次")
    print(f"{'='*50}")

    # ── FEG Step 1: Pre-flight Hook ──
    print(f"\n🔍 Pre-flight Hook:")
    preflight_warnings = hook_preflight()
    for w in preflight_warnings:
        print(f"  {w}")
    critical = [w for w in preflight_warnings if w.startswith("❌")]
    if critical:
        print(f"\n❌ Pre-flight 失敗，中止")
        sys.exit(1)

    # ── FEG Step 2: 逐場景 State Machine ──
    video_files = []
    skipped_scenes = []
    failed_scenes = []
    errors = []
    total_success = 0
    total_skipped = 0
    total_failed = 0

    for i in range(scene_count):
        scene = scenes[i % len(scenes)]
        current_state = STATE_QUEUED
        retry_count = 0
        img_url = None
        video_url = None
        scene_out = None

        print(f"\n{'─'*40}")
        print(f"📌 場景 {i+1}/{scene_count}: {scene['title']}")
        print(f"   初始狀態: {current_state}")
        print(f"{'─'*40}")

        while current_state not in (STATE_COMPLETE, STATE_SKIPPED, STATE_FAILED):
            next_state = current_state  # default: stay

            if current_state == STATE_IMAGE_GEN:
                next_state, img_url = state_image_gen(scene, i)
                if next_state == STATE_IMAGE_DONE:
                    # Hook: Post-image
                    if hook_post_image(img_url):
                        current_state = STATE_IMAGE_DONE
                    else:
                        next_state = STATE_RETRY_IMAGE

            elif current_state == STATE_IMAGE_DONE:
                current_state = STATE_VIDEO_GEN

            elif current_state == STATE_VIDEO_GEN:
                next_state, video_url = state_video_gen(img_url, scene, i, args.duration)
                if next_state == STATE_VIDEO_DONE:
                    # Hook: Post-video
                    if hook_post_video(video_url):
                        current_state = STATE_DOWNLOADING
                    else:
                        next_state = STATE_RETRY_VIDEO

            elif current_state == STATE_DOWNLOADING:
                next_state, scene_out = state_download(video_url, i, run_id)
                if next_state == STATE_COMPLETE:
                    current_state = STATE_COMPLETE
                else:
                    current_state = STATE_RETRY_VIDEO

            elif current_state == STATE_RETRY_IMAGE:
                retry_count += 1
                if retry_count < args.max_retries:
                    print(f"  🔄 重試 {retry_count}/{args.max_retries}...")
                    current_state = STATE_IMAGE_GEN
                else:
                    print(f"  ⏭️ 超過最大重試次數，跳過")
                    errors.append({"scene": i, "title": scene["title"], "phase": "image", "retries": retry_count})
                    current_state = STATE_SKIPPED

            elif current_state == STATE_RETRY_VIDEO:
                retry_count += 1
                if retry_count < args.max_retries:
                    print(f"  🔄 重試 {retry_count}/{args.max_retries}...")
                    current_state = STATE_VIDEO_GEN if not img_url else STATE_POLLING
                else:
                    print(f"  ⏭️ 超過最大重試次數，跳過")
                    errors.append({"scene": i, "title": scene["title"], "phase": "video", "retries": retry_count})
                    current_state = STATE_SKIPPED

            elif current_state == STATE_QUEUED:
                current_state = STATE_IMAGE_GEN

            else:
                print(f"  ⚠️ 未知狀態: {current_state}")
                current_state = STATE_FAILED

            # Safety: prevent infinite loops
            HOLDING_STATES = {STATE_COMPLETE, STATE_SKIPPED, STATE_FAILED, STATE_POLLING, STATE_IMAGE_DONE, STATE_VIDEO_DONE, STATE_QUEUED}
            if current_state == next_state and current_state not in HOLDING_STATES:
                print(f"  ⚠️ 狀態未變更 ({current_state})，強制跳過")
                current_state = STATE_SKIPPED
                break

        # Record result
        if current_state == STATE_COMPLETE and scene_out:
            video_files.append(scene_out)
            total_success += 1
            print(f"  ✅ 場景完成")
        elif current_state == STATE_SKIPPED:
            skipped_scenes.append(i)
            total_skipped += 1
        else:
            failed_scenes.append(i)
            total_failed += 1

    # ── FEG Step 3: Pre-concat Hook ──
    action = hook_pre_concat(video_files, skipped_scenes)

    final_path = None
    if action == "concat":
        final_path = state_concat(video_files, run_id)
    elif action == "single":
        final_path = video_files[0]
        print(f"\n📁 單場景輸出: {final_path}")
    else:
        print("\n❌ 無成功場景")

    # ── FEG Step 4: Post-completion Hook ──
    stats = {
        "total": scene_count,
        "success": total_success,
        "skipped": total_skipped,
        "failed": total_failed,
        "total_duration": total_success * args.duration,
        "errors": errors,
    }
    hook_post_completion(stats, run_id)

    if final_path:
        print(f"\n📁 最終輸出: {final_path}")
        print(f"   MEDIA:{final_path}")


if __name__ == "__main__":
    main()
