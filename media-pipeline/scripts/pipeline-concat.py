#!/usr/bin/env python3
"""
media-pipeline-concat — 多場景影片拼接流水線
1. 文生圖 (Agnes Image 2.1 Flash)
2. 圖生影 (Agnes Video V2.0)
3. 下載各場景影片
4. ffmpeg 串接 → 長影片
"""
import os, sys, json, time, argparse, re, subprocess, uuid
from pathlib import Path
import httpx
from typing import Optional

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
ENV_PATH = os.path.expanduser("~/.hermes/env/agnes.env")

# ── 讀取 Agnes Key ──
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

# ✅ Agnes uses Authorization: Bearer, NOT x-api-key
HEADERS = {"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"}
AGNES_BASE = "https://apihub.agnes-ai.com"
AGNES_API = f"{AGNES_BASE}/v1"

# ── 場景腳本 (可被 --scenes-file 覆蓋) ──
DEFAULT_SCENES = [
  {
    "title": "開場 — 舞台聚光燈",
    "prompt": "Anime idol girl standing on center stage under a single spotlight, long pastel pink twintails, sparkling idol costume with ruffles and ribbons, stage lights creating lens flare, dark auditorium background, cinematic angle from slightly below, professional anime key visual style, high detail, vibrant colors"
  },
  {
    "title": "主歌 — 深情歌唱",
    "prompt": "Close-up of anime idol girl singing into microphone, blue eyes sparkling with emotion, gentle smile, stage lighting creating rim light on hair, soft bokeh background with audience glow, subtle sparkle effects in air, anime idol music video style, smooth facial animation, warm atmosphere"
  },
  {
    "title": "副歌 — 舞蹈動作",
    "prompt": "Dynamic mid-shot of anime idol dancing energetically on stage, twintails flowing with motion, colorful stage lights flashing rainbow, sparkle particles floating, cheerful expression, idol group choreography pose, concert stage with LED screens behind, motion blur effect on hands, energetic anime MV style"
  },
  {
    "title": "尾聲 — 綻放笑容",
    "prompt": "Wide shot of anime idol waving to audience on grand stage, confetti falling from above, huge smile, stage glow creating silhouette effect, warm golden lighting, happy ending atmosphere, performance conclusion, cinematic wide angle, anime concert finale style, emotional victorious feel"
  }
]

def load_scenes(scenes_file: Optional[str] = None) -> list:
    if scenes_file and os.path.isfile(scenes_file):
        with open(scenes_file) as f:
            return json.load(f)
    return DEFAULT_SCENES

def generate_image(scene, scene_idx):
    """文生圖 → 回傳圖片 URL"""
    print(f"\n🎨 [{scene['title']}] 生成圖片中...")
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": scene["prompt"],
        "size": "768x1152",  # 720p 比例
        "n": 1,
    }
    r = httpx.post(f"{AGNES_API}/images/generations",
                   headers=HEADERS, json=payload, timeout=120)
    data = r.json()
    img_url = data.get("data", [{}])[0].get("url", "")
    if not img_url:
        print(f"❌ 圖片生成失敗: {json.dumps(data, indent=2)[:200]}")
        return None
    print(f"✅ 圖片完成: {img_url[:80]}...")
    return img_url


def create_video_task(image_url, scene, scene_idx, duration=5):
    """圖生影任務"""
    fps = 24
    num_frames = duration * fps
    # 確保 8n+1 規則
    num_frames = ((num_frames - 1) // 8) * 8 + 1
    num_frames = min(num_frames, 441)

    print(f"\n🎬 [{scene['title']}] 建立影片任務 ({num_frames}幀 ~{num_frames//fps}秒)...")
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": scene["prompt"],
        "image": image_url,
        "num_frames": num_frames,
        "frame_rate": fps,
    }
    r = httpx.post(f"{AGNES_API}/videos",
                   headers=HEADERS, json=payload, timeout=60)
    data = r.json()
    task_id = data.get("task_id", "")
    video_id = data.get("video_id", "")
    if not task_id:
        print(f"❌ 影片任務建立失敗: {json.dumps(data, indent=2)[:200]}")
        return None
    print(f"✅ 任務已建立: video_id={video_id}")
    return video_id


def poll_video(video_id, scene, scene_idx, timeout=300):
    """輪詢直到完成"""
    print(f"⏳ [{scene['title']}] 渲染中...", end="", flush=True)
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
            # ✅ url 是正確欄位；remixed_from_video_id 常為 null
            video_url = data.get("url", "") or data.get("remixed_from_video_id", "")
            if video_url:
                print(f"\n✅ [{scene['title']}] 完成!")
                return video_url
        elif status in ("failed", "error"):
            print(f"\n❌ [{scene['title']}] 失敗: {data.get('error', 'unknown')}")
            return None
        time.sleep(10)
    print(f"\n⏰ [{scene['title']}] 輪詢超時")
    return None


def download_video(url, output_path):
    """下載影片"""
    print(f"📥 下載影片...")
    r = httpx.get(url, timeout=120)
    if r.status_code != 200:
        print(f"❌ 下載失敗: HTTP {r.status_code}")
        return False
    output_path.write_bytes(r.content)
    size = output_path.stat().st_size
    print(f"✅ 已儲存: {output_path.name} ({size/1024/1024:.1f}MB)")
    return True


def concat_videos(video_files, output_path):
    """ffmpeg 串接影片"""
    print(f"\n🔗 串接 {len(video_files)} 個場景...")
    filelist = OUTPUT_DIR / "concat_list.txt"
    filelist.write_text("\n".join(f"file '{f.name}'" for f in video_files))

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(filelist),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"❌ ffmpeg 失敗: {result.stderr[-300:]}")
        return False
    size = output_path.stat().st_size
    print(f"✅ 最終影片: {output_path.name} ({size/1024/1024:.1f}MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="多場景影片拼接流水線")
    parser.add_argument("--duration", type=int, default=5, help="每場景秒數 (1-18)")
    parser.add_argument("--scenes", type=int, default=4, help="場景數 (1-10)")
    parser.add_argument("--topic", type=str, default="偶像歌唱", help="主題描述")
    parser.add_argument("--scenes-file", type=str, default="", help="自訂場景 JSON 檔案路徑")
    args = parser.parse_args()

    scenes = load_scenes(args.scenes_file)
    scene_count = min(args.scenes, len(scenes)) if len(scenes) >= args.scenes else args.scenes

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())[:8]
    print(f"\n{'='*50}")
    print(f"🎬 media-pipeline-concat (run_id={run_id})")
    print(f"   主題: {args.topic}")
    print(f"   場景: {scene_count} 場景 × {args.duration}秒")
    print(f"{'='*50}\n")

    video_files = []
    for i in range(scene_count):
        scene = scenes[i % len(scenes)]
        print(f"\n{'─'*40}")
        print(f"📌 場景 {i+1}/{scene_count}: {scene['title']}")
        print(f"{'─'*40}")

        # Step 1: 文生圖
        img_url = generate_image(scene, i)
        if not img_url:
            continue

        # Step 2: 圖生影
        video_id = create_video_task(img_url, scene, i, args.duration)
        if not video_id:
            continue

        # Step 3: 輪詢
        video_url = poll_video(video_id, scene, i)
        if not video_url:
            continue

        # Step 4: 下載
        out_path = OUTPUT_DIR / f"scene_{i+1:02d}_{run_id}.mp4"
        if download_video(video_url, out_path):
            video_files.append(out_path)

    # Step 5: 串接
    if len(video_files) >= 2:
        final_path = OUTPUT_DIR / f"final_{run_id}.mp4"
        if concat_videos(video_files, final_path):
            total_sec = len(video_files) * args.duration
            print(f"\n{'='*50}")
            print(f"🎉 完成! {len(video_files)} 場景, 共 ~{total_sec}秒")
            print(f"📁 {final_path}")
            print(f"{'='*50}")
        else:
            print("\n⚠️ 串接失敗，各場景影片仍可單獨使用")
    elif len(video_files) == 1:
        print(f"\n⚠️ 只有 1 個場景成功，無需串接")
    else:
        print("❌ 所有場景都失敗")


if __name__ == "__main__":
    main()
