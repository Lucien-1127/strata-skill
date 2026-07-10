#!/usr/bin/env python3
"""
media-pipeline v2.1 — Agnes Video API 正確版

金鑰從 ~/.hermes/env/agnes.env 讀取（不在 repo 內）。
支援中斷恢復、多場景轉場、結構化 JSON 輸出。
"""
import os, sys, json, time, argparse, asyncio, uuid, re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import httpx

# ── Config ──
BASE_DIR = Path(__file__).parent.resolve()
STATE_FILE = BASE_DIR / "agents_workflow_state.json"
SCENE_FILE = BASE_DIR / "scene_prompts.json"
OUTPUT_DIR = BASE_DIR / "output"
SCENES_DIR = OUTPUT_DIR / "scenes"
VIDEOS_DIR = OUTPUT_DIR / "videos"

AGNES_BASE = "https://apihub.agnes-ai.com"
AGNES_API = f"{AGNES_BASE}/v1"
AGNES_IMG_MODEL = "agnes-image-2.1-flash"
AGNES_VIDEO_MODEL = "agnes-video-v2.0"
AGNES_TEXT_MODEL = "agnes-2.0-flash"

# ── 金鑰：從 ~/.hermes/env/agnes.env 讀取 ──
ENV_PATH = os.path.expanduser("~/.hermes/env/agnes.env")
AGNES_KEY = ""
if os.path.isfile(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            m = re.match(r'^\s*AGNES_API_KEY=(.*)$', line.strip())
            if m:
                AGNES_KEY = m.group(1).strip('"\'')
if not AGNES_KEY:
    print("❌ AGNES_API_KEY not found. Create ~/.hermes/env/agnes.env")
    sys.exit(1)

# ── Duration Presets ──
DURATION_PRESETS = {
    5:  (121, 24, "1080p"),
    7:  (169, 24, "1080p"),
    10: (241, 24, "720p"),
    12: (289, 24, "720p"),
    15: (361, 24, "720p"),
    17: (409, 24, "720p"),
}
RES_9_16 = {
    "1080p": {"width": 1080, "height": 1920},
    "720p":  {"width": 768,  "height": 1152},
}

class PipelineState:
    def __init__(self):
        self.run_id = str(uuid.uuid4())[:8]
        self.current_stage = "INIT"
        self.scene_count = 3
        self.completed_scenes = []
        self.failed_scenes = []
        self.image_urls = {}
        self.video_urls = {}
        self.quota_used_seconds = 0
        self.retry_count = 0

    @classmethod
    def load(cls):
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            s = cls()
            s.__dict__.update(data)
            return s
        return cls()

    def save(self):
        STATE_FILE.write_text(json.dumps(self.__dict__, indent=2, ensure_ascii=False))


class AgnesAPI:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=AGNES_API,
            headers={"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"},
            timeout=120,
        )

    async def chat(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        for attempt in range(4):
            try:
                resp = await self.client.post("/chat/completions", json={
                    "model": AGNES_TEXT_MODEL, "messages": messages, "max_tokens": 4096,
                })
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt); continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Chat API failed")

    async def generate_image(self, prompt: str, size: str = "1024x1792") -> Optional[str]:
        for attempt in range(4):
            try:
                resp = await self.client.post("/images/generations", json={
                    "model": AGNES_IMG_MODEL, "prompt": prompt, "n": 1, "size": size,
                })
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt); continue
                resp.raise_for_status()
                return resp.json()["data"][0]["url"]
            except Exception:
                await asyncio.sleep(2 ** attempt)
        return None

    async def generate_video(self, image_url: str, prompt: str,
                             duration: int = 5,
                             width: int = 768, height: int = 1152) -> Optional[str]:
        nf, fr, res_label = DURATION_PRESETS.get(duration, DURATION_PRESETS[5])
        res = RES_9_16.get(res_label, RES_9_16["720p"])
        payload = {
            "model": AGNES_VIDEO_MODEL,
            "image": image_url,
            "prompt": prompt,
            "num_frames": nf,
            "frame_rate": fr,
            "width": width or res["width"],
            "height": height or res["height"],
        }
        for attempt in range(4):
            try:
                resp = await self.client.post("/videos", json=payload)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt); continue
                resp.raise_for_status()
                data = resp.json()
                return data.get("video_id") or data.get("id")
            except Exception as e:
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"  ❌ 影片提交失敗: {e}")
                    return None
        return None

    async def generate_multi_image_video(self, image_urls: list, prompt: str,
                                         duration: int = 5) -> Optional[str]:
        nf, fr, res_label = DURATION_PRESETS.get(duration, DURATION_PRESETS[5])
        res = RES_9_16.get(res_label, RES_9_16["720p"])
        payload = {
            "model": AGNES_VIDEO_MODEL,
            "prompt": prompt,
            "num_frames": nf,
            "frame_rate": fr,
            "width": res["width"],
            "height": res["height"],
            "extra_body": {"image": image_urls}
        }
        for attempt in range(4):
            try:
                resp = await self.client.post("/videos", json=payload)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt); continue
                resp.raise_for_status()
                data = resp.json()
                return data.get("video_id") or data.get("id")
            except Exception:
                await asyncio.sleep(2 ** attempt)
        return None

    async def poll_video(self, video_id: str, timeout: int = 300) -> Optional[str]:
        start = time.time()
        while time.time() - start < timeout:
            try:
                async with httpx.AsyncClient(timeout=30) as pc:
                    resp = await pc.get(
                        f"{AGNES_BASE}/agnesapi",
                        params={"video_id": video_id, "model_name": AGNES_VIDEO_MODEL},
                        headers={"Authorization": f"Bearer {AGNES_KEY}"})
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "")
                    if status == "completed":
                        url = (data.get("remixed_from_video_id")
                               or data.get("url")
                               or data.get("output", {}).get("url"))
                        if url:
                            return url
                    elif status in ("failed", "error"):
                        print(f"  ❌ 影片失敗: {data.get('error', 'unknown')}")
                        return None
            except Exception as e:
                print(f"  ⚠️ 輪詢異常: {e}")
            await asyncio.sleep(5)
        print(f"  ⏰ 影片 {video_id} 輪詢超時")
        return None

    async def close(self):
        await self.client.aclose()


async def write_script_v2(api: AgnesAPI, topic: str, scene_count: int) -> list[dict]:
    system = (
        "你是一個專業影片分鏡腳本寫手。輸出 JSON 陣列，每個元素包含：\n"
        "- scene_id: 整數編號 (0-based)\n"
        "- scene_title: 場景標題\n"
        "- scene_goal: 這個場景要傳達什麼\n"
        "- visual_style: 視覺風格描述\n"
        "- image_prompt: 英文圖片提示詞（Agnes Image 2.1 Flash，9:16 直式）\n"
        "- video_prompt: 英文影片動態描述（Agnes Video v2.0）\n"
        "- transition_rule: 轉場方式 (dissolve/cut/wipe/morph)\n"
        "- duration_seconds: 5-15 秒\n"
        "- width: 768\n"
        "- height: 1152\n\n"
        "重點：場景之間要有視覺連續性。輸出純 JSON 陣列，不要 markdown。"
    )
    prompt = (
        f"請為主題「{topic}」設計 {scene_count} 個連續分鏡腳本。\n"
        "要求：\n1. 場景之間要有視覺連續性\n"
        "2. 每個場景的 image_prompt 要考慮前一場景的視覺元素\n"
        "3. 9:16 直式\n4. duration_seconds 在 5-15 秒之間\n"
        "輸出純 JSON 陣列。"
    )
    try:
        text = await api.chat(prompt, system=system)
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        scenes = json.loads(text)
        if isinstance(scenes, list):
            return scenes
    except Exception as e:
        print(f"⚠️ 腳本生成失敗: {e}")
    return [
        {"scene_id": i, "scene_title": f"Scene {i+1}",
         "scene_goal": f"展示{topic}場景{i+1}",
         "visual_style": "Cinematic, vibrant",
         "image_prompt": f"Cinematic shot of {topic}, scene {i+1}, 9:16 portrait, vibrant colors, 4k",
         "video_prompt": f"Slow cinematic pan, smooth motion, {topic} scene {i+1}",
         "transition_rule": "dissolve" if i > 0 else "cut",
         "duration_seconds": 10,
         "width": 768, "height": 1152}
        for i in range(scene_count)
    ]


async def main():
    parser = argparse.ArgumentParser(description="Media Pipeline v2.1")
    parser.add_argument("--reset", action="store_true", help="重置狀態")
    parser.add_argument("--scenes", type=int, default=3, help="分鏡數")
    parser.add_argument("--duration", type=int, default=10, help="每場景秒數(5-15)")
    parser.add_argument("--topic", default=None, help="主題")
    parser.add_argument("--structured", action="store_true", help="輸出結構化 JSON")
    parser.add_argument("--multi-image", action="store_true", help="多圖轉場模式")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENES_DIR.mkdir(exist_ok=True)
    VIDEOS_DIR.mkdir(exist_ok=True)

    if args.reset:
        for p in [STATE_FILE, SCENE_FILE]:
            if p.exists(): p.unlink()
        state = PipelineState()
    else:
        state = PipelineState.load()

    api = AgnesAPI()
    run_id = state.run_id

    try:
        # Phase 1: Script
        if state.current_stage == "INIT":
            print(f"\n📝 Phase 1: Script ({args.scenes} scenes)")
            topic = args.topic or input("主題: ").strip() or "城市夜景到魔幻仙境"
            scenes = await write_script_v2(api, topic, args.scenes)
            SCENE_FILE.write_text(json.dumps(scenes, indent=2, ensure_ascii=False))
            state.scene_count = len(scenes)
            state.current_stage = "SCRIPT_DONE"
            state.save()
            (OUTPUT_DIR / "script_package.json").write_text(
                json.dumps({"run_id": run_id, "theme": topic,
                           "total_scenes": len(scenes), "scenes": scenes},
                          indent=2, ensure_ascii=False))
        else:
            scenes = json.loads(SCENE_FILE.read_text()) if SCENE_FILE.exists() else []

        # Phase 2: Images
        if state.current_stage == "SCRIPT_DONE":
            print(f"\n🖼️ Phase 2: Generate {len(scenes)} images")
            state.current_stage = "IMAGE_GEN"
            state.save()
            image_jobs = {"run_id": run_id, "jobs": []}
            for i, scene in enumerate(scenes):
                si = str(i)
                if si in state.image_urls:
                    print(f"  ✅ Scene {i} image exists, skip")
                    continue
                print(f"  🖼️ Scene {i}: {scene.get('scene_title', '')}")
                url = await api.generate_image(scene["image_prompt"], size="1024x1792")
                if url:
                    state.image_urls[si] = url
                    state.completed_scenes.append(i)
                else:
                    state.failed_scenes.append(i)
                image_jobs["jobs"].append({
                    "scene_id": i, "status": "completed" if url else "failed",
                    "image_url": url or "",
                })
                state.save()
            (OUTPUT_DIR / "image_jobs.json").write_text(
                json.dumps(image_jobs, indent=2, ensure_ascii=False))
            state.current_stage = "IMAGE_DONE"
            state.save()

        # Phase 3: Video
        if state.current_stage == "IMAGE_DONE":
            print(f"\n🎬 Phase 3: Generate video")
            state.current_stage = "VIDEO_GEN"
            state.save()
            image_list = [state.image_urls.get(str(i), "")
                          for i in range(state.scene_count)]
            image_list = [u for u in image_list if u]
            video_jobs = {"run_id": run_id, "jobs": []}

            if args.multi_image and len(image_list) >= 2:
                print("  🔗 Multi-image transition mode")
                transition_prompt = (
                    f"Smooth cinematic transition across {len(image_list)} scenes. "
                    f"9:16 portrait, cinematic lighting, smooth motion.")
                video_id = await api.generate_multi_image_video(
                    image_list, transition_prompt, duration=args.duration)
                if video_id:
                    print("  ⏳ Polling multi-image video...")
                    url = await api.poll_video(video_id, timeout=300)
                    if url:
                        state.video_urls["0"] = url
                        state.quota_used_seconds += args.duration
                    video_jobs["jobs"].append({
                        "scene_id": "all", "mode": "multi-image",
                        "video_id": video_id, "status": "completed" if url else "failed",
                        "output_url": url or "",
                    })
            else:
                for i, img_url in enumerate(image_list):
                    si = str(i)
                    if si in state.video_urls:
                        print(f"  ✅ Scene {i} video exists, skip")
                        continue
                    scene = scenes[i] if i < len(scenes) else {}
                    print(f"  🎬 Scene {i}: {scene.get('scene_title', '')} ({args.duration}s)")
                    dur = min(scene.get("duration_seconds", args.duration), 15)
                    video_id = await api.generate_video(
                        img_url, scene.get("video_prompt", "Cinematic motion"), duration=dur)
                    if video_id:
                        print("  ⏳ Polling...")
                        url = await api.poll_video(video_id, timeout=300)
                        if url:
                            state.video_urls[si] = url
                            state.quota_used_seconds += dur
                        video_jobs["jobs"].append({
                            "scene_id": i, "mode": "image-to-video",
                            "video_id": video_id, "status": "completed" if url else "failed",
                            "output_url": url or "",
                        })
                    state.save()
            (OUTPUT_DIR / "video_jobs.json").write_text(
                json.dumps(video_jobs, indent=2, ensure_ascii=False))
            state.current_stage = "VIDEO_DONE"
            state.save()

        # Complete
        state.current_stage = "COMPLETE"
        state.save()
        notify = {
            "run_id": run_id,
            "overall_status": "completed" if not state.failed_scenes else "partial",
            "completed_scenes": len(state.video_urls),
            "failed_scenes": len(state.failed_scenes),
            "output_urls": list(state.video_urls.values()),
            "quota_used_seconds": state.quota_used_seconds,
            "message": (f"✅ {len(state.video_urls)}/{state.scene_count} videos completed"
                        if not state.failed_scenes else
                        f"⚠️ Partial: {len(state.video_urls)}/{state.scene_count}"),
        }
        (OUTPUT_DIR / "notify_payload.json").write_text(
            json.dumps(notify, indent=2, ensure_ascii=False))
        print(f"\n{'='*50}\n{notify['message']}")
        print(f"  Videos: {len(state.video_urls)}/{state.scene_count}")
        print(f"  Failed: {len(state.failed_scenes)}")
        if args.structured:
            print(f"  Output: {OUTPUT_DIR}/")
    except Exception as e:
        state.last_error = str(e)
        state.save()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())
