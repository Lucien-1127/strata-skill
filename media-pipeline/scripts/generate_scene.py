#!/usr/bin/env python3
"""Generate one scene video via Agnes API and download the result."""
import requests
import time
import sys
import os
import json

API_KEY = os.environ.get("AGNES_API_KEY")
if not API_KEY:
    print("ERROR: AGNES_API_KEY not set", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

CREATE_URL = "https://apihub.agnes-ai.com/v1/videos"
POLL_TEMPLATE = "https://apihub.agnes-ai.com/agnesapi?video_id={video_id}&model_name=agnes-video-v2.0"

NEGATIVE_PROMPT = (
    "different character, face change, identity change, face morphing, "
    "different hairstyle, different outfit, appearance drift, character mutation, "
    "swapped identity, face distortion, ugly, deformed, bad anatomy, blurry, "
    "jittery, distorted, inconsistent, low quality"
)

def create_video(image_url, prompt):
    payload = {
        "model": "agnes-video-v2.0",
        "image": image_url,
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "num_frames": 121,
        "frame_rate": 24,
        "width": 576,
        "height": 1024,
    }
    print(f"  Creating video task...", flush=True)
    resp = requests.post(CREATE_URL, json=payload, headers=HEADERS, timeout=60)
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {resp.text[:1000]}", file=sys.stderr, flush=True)
        sys.exit(1)
    data = resp.json()
    print(f"  Create response: {json.dumps(data, indent=2)[:500]}", flush=True)
    
    # Try different possible field names for video_id
    video_id = None
    if isinstance(data, dict):
        video_id = data.get("data", {}).get("video_id") or data.get("video_id") or data.get("id")
        # Also check if data is nested differently
        if not video_id and "data" in data and isinstance(data["data"], dict):
            video_id = data["data"].get("id")
    if not video_id:
        print(f"  ERROR: Could not extract video_id from response: {json.dumps(data, indent=2)}", file=sys.stderr)
        sys.exit(1)
    print(f"  Got video_id: {video_id}", flush=True)
    return video_id

def poll_video(video_id, timeout=600):
    poll_url = POLL_TEMPLATE.format(video_id=video_id)
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"  ERROR: Poll timeout after {timeout}s", file=sys.stderr)
            sys.exit(1)
        
        resp = requests.get(poll_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        status = None
        video_url = None
        
        if isinstance(data, dict):
            status = data.get("data", {}).get("status") or data.get("status")
            video_url = data.get("data", {}).get("url") or data.get("url")
        
        print(f"  [{elapsed:.0f}s] status={status}, has_url={bool(video_url)}", flush=True)
        
        if status == "completed" or status == "succeeded" or video_url:
            # Once we have a URL, it's done
            video_url = data.get("data", {}).get("url", "") or data.get("url", "")
            if not video_url:
                # Try deeper nesting
                d = data.get("data", {})
                if isinstance(d, dict):
                    video_url = d.get("url", "")
            if video_url:
                print(f"  Video URL: {video_url}", flush=True)
                return video_url
        
        if status in ("failed", "error"):
            error_msg = data.get("data", {}).get("error", data.get("error", "Unknown error"))
            print(f"  ERROR: Video generation failed: {error_msg}", file=sys.stderr)
            print(f"  Full response: {json.dumps(data, indent=2)}", file=sys.stderr)
            sys.exit(1)
        
        time.sleep(10)

def download_video(url, output_path):
    print(f"  Downloading to {output_path}...", flush=True)
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Downloaded: {size_mb:.1f} MB", flush=True)
    return output_path

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <scene_name> <image_url> <prompt>", file=sys.stderr)
        sys.exit(1)
    
    scene_name = sys.argv[1]
    image_url = sys.argv[2]
    prompt = sys.argv[3]
    
    output_dir = "/home/ysga1/.hermes/skills/media-pipeline/scripts/output/"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{scene_name}.mp4")
    
    print(f"\n=== Generating {scene_name} ===", flush=True)
    
    # If already exists, skip
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
        print(f"  Already exists: {output_path} ({os.path.getsize(output_path)/(1024*1024):.1f} MB)", flush=True)
        print(f"RESULT:{output_path}")
        return
    
    video_id = create_video(image_url, prompt)
    video_url = poll_video(video_id)
    download_video(video_url, output_path)
    print(f"RESULT:{output_path}", flush=True)

if __name__ == "__main__":
    main()
