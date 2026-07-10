#!/usr/bin/env python3
"""
idol-video-pipeline — 以參考圖片為基礎的影片生成流水線
使用使用者提供的角色圖片作為每場景的起始幀，保持角色一致性
"""
import os, sys, json, time, argparse, re, subprocess, uuid
from pathlib import Path
import httpx

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
ENV_PATH = os.path.expanduser("~/.hermes/env/agnes.env")

# ── Agnes Key ──
AGNES_KEY = ""
if os.path.isfile(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            m = re.match(r'^\s*AGNES_API_KEY=(.*)$', line.strip())
            if m:
                AGNES_KEY = m.group(1).strip('"\'')
if not AGNES_KEY:
    print("❌ AGNES_API_KEY not found")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"}
AGNES_BASE = "https://apihub.agnes-ai.com"
AGNES_API = f"{AGNES_BASE}/v1"


def create_video_task(ref_image_url, scene, scene_idx, duration=5):
    """圖生影 — 使用參考圖片作為起始幀"""
    fps = 24
    num_frames = duration * fps
    num_frames = ((num_frames - 1) // 8) * 8 + 1  # 8n+1 rule
    num_frames = min(num_frames, 441)
    real_sec = num_frames / fps
    print(f"\n🎬 [{scene['title']}] ({real_sec:.1f}秒, {num_frames}幀)...")
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": scene["prompt"],
        "image": ref_image_url,
        "num_frames": num_frames,
        "frame_rate": fps,
        "negative_prompt": "different character, face change, identity change, face morphing, different body shape, different color, appearance drift, character mutation, inconsistent appearance, ugly, deformed, bad anatomy, blurry, jittery, distorted, low quality",
    }
    r = httpx.post(f"{AGNES_API}/videos", headers=HEADERS, json=payload, timeout=60)
    data = r.json()
    video_id = data.get("video_id", "")
    if not video_id:
        print(f"❌ 失敗: {json.dumps(data, indent=2)[:200]}")
        return None
    print(f"✅ video_id={video_id}")
    return video_id


def poll_video(video_id, scene, scene_idx, timeout=600):
    """輪詢直到完成（預設 10 分鐘）
    
    NOTE: /agnesapi 回應中 video URL 在 url 欄位（非 remixed_from_video_id）。
    remixed_from_video_id 經常為 null，須改讀 url。
    """
    print(f"⏳ 渲染中", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = httpx.get(
            f"{AGNES_BASE}/agnesapi",
            params={"video_id": video_id, "model_name": "agnes-video-v2.0"},
            headers=HEADERS, timeout=30
        )
        data = r.json()
        status = data.get("status", "unknown")
        print(".", end="", flush=True)
        if status == "completed":
            # url 是正確的影片下載連結（remixed_from_video_id 常為 null）
            video_url = data.get("url", "") or data.get("remixed_from_video_id", "")
            if video_url:
                print(f"\n✅ 完成! {data.get('seconds', '?')}秒, {data.get('size', '?')}")
                return video_url
        elif status in ("failed", "error"):
            print(f"\n❌ 失敗: {data.get('error', 'unknown')}")
            return None
        time.sleep(8)
    print(f"\n⏰ 超時 (>{timeout}秒)")
    return None


def download_video(url, output_path):
    print(f"📥 下載...", end="", flush=True)
    r = httpx.get(url, timeout=120)
    if r.status_code != 200:
        print(f" ❌ HTTP {r.status_code}")
        return False
    output_path.write_bytes(r.content)
    size = output_path.stat().st_size
    print(f" ✅ {output_path.name} ({size/1024/1024:.1f}MB)")
    return True


def concat_videos(video_files, output_path, crossfade=False, duration=5):
    """ffmpeg 串接，可選 crossfade 轉場"""
    n = len(video_files)
    print(f"\n🔗 串接 {n} 個場景...")
    if crossfade and n >= 2:
        offset = duration - 1  # crossfade starts 1s before scene end
        filter_parts = [f"[0:v]format=yuv420p[v0]"]
        for i in range(1, n):
            actual_offset = i * (duration - 1)
            filter_parts.append(
                f"[v{i-1}][{i}:v]xfade=transition=fade:duration=1:offset={actual_offset}[v{i}]"
            )
        filter_chain = "; ".join(filter_parts)
        cmd = (
            f"ffmpeg -y {' '.join(f'-i \"{f}\"' for f in video_files)} "
            f"-filter_complex \"{filter_chain}\" "
            f"-map \"[v{n-1}]\" -c:v libx264 -preset medium -crf 18 "
            f"-pix_fmt yuv420p \"{output_path}\""
        )
    else:
        filelist = OUTPUT_DIR / "concat_list.txt"
        filelist.write_text("\n".join(f"file '{f.name}'" for f in video_files))
        cmd = (
            f"ffmpeg -y -f concat -safe 0 "
            f"-i \"{filelist}\" "
            f"-c:v libx264 -preset medium -crf 18 "
            f"-pix_fmt yuv420p \"{output_path}\""
        )
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, shell=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg: {result.stderr[-300:]}")
        return False
    size = output_path.stat().st_size
    print(f"✅ 最終影片: {output_path.name} ({size/1024/1024:.1f}MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="🎤 動畫偶像影片流水線")
    parser.add_argument("--ref-image", type=str, required=True,
                        help="角色參考圖片 URL（必要）")
    parser.add_argument("--scenes-file", type=str, default="",
                        help="場景腳本 JSON 檔案路徑（選用，預設使用內建腳本）")
    parser.add_argument("--duration", type=int, default=5, help="每場景秒數 (1-18)")
    parser.add_argument("--scenes", type=int, default=4, help="場景數")
    parser.add_argument("--crossfade", action="store_true", help="啟用 crossfade 轉場")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())[:8]

    # 載入場景腳本
    if args.scenes_file and os.path.isfile(args.scenes_file):
        with open(args.scenes_file) as f:
            scenes = json.load(f)
        scene_count = min(args.scenes, len(scenes))
    else:
        scenes = [{"title": f"場景 {i+1}", "prompt": ""} for i in range(args.scenes)]
        scene_count = args.scenes

    print(f"\n{'='*55}")
    print(f"🎤 動畫偶像影片流水線 (run_id={run_id})")
    print(f"   場景: {scene_count} 場景 × {args.duration}秒")
    print(f"   轉場: {'crossfade' if args.crossfade else '硬切'}")
    print(f"{'='*55}")

    video_files = []
    for i in range(scene_count):
        scene = scenes[i % len(scenes)]
        print(f"\n{'─'*45}")
        print(f"📌 場景 {i+1}/{scene_count}: {scene.get('title', f'場景 {i+1}')}")
        print(f"{'─'*45}")

        video_id = create_video_task(args.ref_image, scene, i, args.duration)
        if not video_id:
            continue

        video_url = poll_video(video_id, scene, i)
        if not video_url:
            continue

        out_path = OUTPUT_DIR / f"scene_{i+1:02d}_{run_id}.mp4"
        if download_video(video_url, out_path):
            video_files.append(out_path)

    # 串接
    if len(video_files) >= 2:
        final_path = OUTPUT_DIR / f"final_{run_id}.mp4"
        if concat_videos(video_files, final_path, args.crossfade, args.duration):
            total = len(video_files) * args.duration
            print(f"\n{'='*55}")
            print(f"🎉 完成! {len(video_files)} 場景, ~{total}秒")
            print(f"📁 {final_path}")
            print(f"{'='*55}")
        else:
            print("\n⚠️ 串接失敗，各場景單獨可用")
    elif len(video_files) == 1:
        print(f"\n📁 單場景: {video_files[0]}")
    else:
        print("\n❌ 所有場景失敗")


if __name__ == "__main__":
    main()
