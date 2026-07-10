# 無頭 VM 瀏覽器 + VNC 設定

用於需要桌面瀏覽器操作的場景（如 Canva Developer Portal 僅支援桌面版）。

## 安裝步驟

```bash
# 1. 安裝 Xvfb（虛擬 framebuffer）
sudo apt-get install -y xvfb

# 2. 安裝瀏覽器（Chromium snap）
sudo apt-get install -y chromium-browser

# 3. 安裝 VNC 伺服器
sudo apt-get install -y x11vnc

# 4. 安裝截圖工具（可選）
sudo apt-get install -y imagemagick
```

## 啟動

```bash
# 1. 啟動 Xvfb（虛擬顯示器 :99）
Xvfb :99 -screen 0 1920x1080x24 &

# 2. 設定 VNC 密碼
mkdir -p ~/.vnc
x11vnc -storepasswd <密碼> ~/.vnc/passwd

# 3. 啟動 VNC
export DISPLAY=:99
x11vnc -display :99 -forever -shared -rfbauth ~/.vnc/passwd -rfbport 15999 &

# 4. 啟動瀏覽器
export DISPLAY=:99
chromium-browser --no-sandbox --start-maximized "https://目標網址" &
```

## 防火牆

```bash
# UFW
sudo ufw allow 15999/tcp

# GCP（如適用）
gcloud compute firewall-rules create allow-vnc \
  --direction=INGRESS --priority=1000 --network=default \
  --action=ALLOW --rules=tcp:15999 \
  --source-ranges=0.0.0.0/0
```

## 手機連線

- 主機：VM 公開 IP
- 連接埠：15999
- 用戶端：RealVNC / Mocha VNC（iOS/Android）

## 截圖檢查

```bash
export DISPLAY=:99
import -window root /tmp/screenshot.png
```

## 清理

```bash
sudo ufw delete allow 15999/tcp
gcloud compute firewall-rules delete allow-vnc --quiet
kill $(pgrep -f x11vnc) $(pgrep -f Xvfb) $(pgrep -f chromium) 2>/dev/null
```

## 替代方案

Tailscale：`curl -fsSL https://tailscale.com/install.sh | sh` → `sudo tailscale up`
透過 Tailscale IP 走加密通道，不需開公開防火牆。
