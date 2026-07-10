#!/usr/bin/env python3
"""Start a cloudflared trycloudflare tunnel to the mini app server and capture the URL.

Usage:
  python3 start-tunnel.py

Output:
  Writes the tunnel URL to stdout and also saves it to ~/.hermes/env/miniapp-tunnel-url.txt

The tunnel runs indefinitely (until killed). Every restart generates a NEW URL
because trycloudflare quick tunnels have no persistence.
"""
import subprocess, sys, os, time, re

def main():
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:8081"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    url = None
    start = time.time()
    timeout = 30

    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if not line:
            continue
        sys.stdout.write(line)
        sys.stdout.flush()
        m = re.search(r'https://[a-z-]+\.trycloudflare\.com', line)
        if m:
            url = m.group(0)
            break

    if url:
        save_path = os.path.expanduser("~/.hermes/env/miniapp-tunnel-url.txt")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            f.write(url)
        print(f"\n{'='*60}")
        print(f"✅ TUNNEL URL: {url}")
        print(f"   Saved to: {save_path}")
        print(f"{'='*60}")
    else:
        print("❌ Failed to get tunnel URL within timeout")

    # Keep tunnel alive
    try:
        while True:
            line = proc.stdout.readline()
            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()

if __name__ == "__main__":
    main()
