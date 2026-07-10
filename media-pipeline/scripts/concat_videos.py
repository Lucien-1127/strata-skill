#!/usr/bin/env python3
"""Scale all scenes to common resolution and concatenate."""
import subprocess, os

output_dir = "/home/ysga1/.hermes/skills/media-pipeline/scripts/output/"
scaled_dir = output_dir + "scaled/"
os.makedirs(scaled_dir, exist_ok=True)

scenes = ["scene_1", "scene_2", "scene_3", "scene_4"]
scaled_files = []

for s in scenes:
    inp = output_dir + s + ".mp4"
    out = scaled_dir + s + "_scaled.mp4"
    scale_cmd = [
        "ffmpeg", "-y", "-i", inp,
        "-vf", "scale=448:832:force_original_aspect_ratio=disable,setsar=1",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        out
    ]
    print(f"Scaling {s}...", flush=True)
    r = subprocess.run(scale_cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"  FAIL: {r.stderr[-200:]}", flush=True)
        sys.exit(1)
    print(f"  OK: {out}", flush=True)
    scaled_files.append(out)

# Create concat list
concat_list = scaled_dir + "concat_list.txt"
with open(concat_list, "w") as f:
    for sf in scaled_files:
        f.write(f"file '{os.path.basename(sf)}'\n")

# Concat
final_path = output_dir + "final_idol.mp4"
concat_cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p",
    final_path
]
print(f"\nConcatenating {len(scaled_files)} scenes...", flush=True)
r = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=600)
if r.returncode != 0:
    print(f"  CONCAT FAIL: {r.stderr[-300:]}", flush=True)
    sys.exit(1)

size_mb = os.path.getsize(final_path) / (1024 * 1024)
print(f"\n✅ Final video: {final_path} ({size_mb:.1f} MB)", flush=True)

# Write path to tmp file
with open("/tmp/final_video_path.txt", "w") as f:
    f.write(final_path + "\n")
print(f"✅ Path saved to /tmp/final_video_path.txt", flush=True)
