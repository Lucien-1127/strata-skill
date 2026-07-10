# CineAgent Pipeline v3.3 — 真正 Frame Chaining（ffmpeg 抽末幀 + 3 層上傳降級）

> Sister repo at `~/CineAgent/` (`git@github.com:Lucien-1127/CineAgent.git`)
> 分支 `main`，最新 commit `e139fed`（2026-07-09）
> 與 `media-pipeline` 同領域但獨立開發，偏向腳本驅動的端到端流程

## v3.2 → v3.3 關鍵差異

| 項目 | v3.2 (舊) | v3.3 (當前) |
|:----|:----------|:------------|
| Frame Chaining 末幀來源 | 影片 URL（proxy，實質無效） | **ffmpeg 真正抽 JPEG 末幀** |
| 末幀上傳方式 | ❌ 無 | 3 層降級（Agnes → imgbb → prompt fallback） |
| frame_chaining | 標記 true 但傳的是影片 URL | ✅ 真實圖片 URL 傳入 end_image |
| output/video_jobs.json 欄位 | `frame_chaining: true/false` | ✅ 新增 `frame_chaining_url`（實際末幀圖片 URL） |
| 需額外環境變數 | 無 | `IMGBB_API_KEY`（imgbb 免費 key，備援上傳用） |
| `--reset` 副作用 | 刪除 `scene_prompts.json` | 同（注意：與 `--skip-script` 互斥） |

## 事前檢查

### ffmpeg 必須安裝

v3.3 用 ffmpeg 從影片中抽取最末幀：

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# 確認
ffmpeg -version | head -1
```

### IMGBB_API_KEY 建議設定（備援上傳）

免費 key：https://api.imgbb.com → Register → API Key

```bash
export IMGBB_API_KEY=你的key
```

若未設定，第一層（Agnes /v1/images/uploads）失敗時將跳過 Frame Chaining，退回純 prompt 文字橋接。

## CLI 參數

```bash
cd ~/CineAgent

# 完整流程（含腳本設計 + Frame Chaining）
export AGNES_API_KEY=$(grep AGNES_API_KEY ~/.hermes/env/agnes.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
export IMGBB_API_KEY=你的key
python run_pipeline.py --topic "主題" --scenes 5 --duration 5 --quality cinematic

# 跳過腳本，直接從 scene_prompts.json 載入
python run_pipeline.py --skip-script --quality cinematic --reset --topic "主題"

# ⚠️ --reset 與 --skip-script 互斥（reset 會刪除 scene_prompts.json）
# 正確用法：先建立 scene_prompts.json，跑時不加 reset 或手動刪 agents_workflow_state.json 保留 scene_prompts.json

# 多圖轉場模式
python run_pipeline.py --multi-image

# 結構化 JSON 輸出
python run_pipeline.py --structured
```

## Frame Chaining 真正實作（v3.3）

### 3 層上傳降級邏輯

每場景影片渲染完成後，v3.3 執行以下流程：

```
影片渲染完成 (video URL)
    │
    ├─ ffmpeg 抽取最後一幀 → /tmp/last_frame_{scene}.jpg
    │
    ├─ Tier 1: Agnes /v1/images/uploads?
    │   ├─ ✅ → 回傳公開 URL → 存入 last_frame_urls
    │   └─ ❌ → 降級到 Tier 2
    │
    ├─ Tier 2: imgbb API?
    │   ├─ ✅ (需 IMGBB_API_KEY) → 回傳公開 URL → 存入 last_frame_urls
    │   └─ ❌ (無 key 或 API 失敗) → 降級到 Tier 3
    │
    └─ Tier 3: 純 prompt 文字橋接
        └─ 只在 video_prompt 注入 chaining_hint，無實際圖片錨點
```

### 核心流程

```python
# 1. ffmpeg 抽末幀
last_frame_path = OUTPUT_DIR / "scenes" / f"last_frame_{scene_id}.jpg"
subprocess.run([
    "ffmpeg", "-y", "-sseof", "-1",
    "-i", video_url,
    "-vframes", "1",
    "-q:v", "3",
    str(last_frame_path)
], capture_output=True, timeout=15)

# 2. 3 層上傳
# Tier 1: Agnes upload endpoint
try:
    resp = await self.client.post("/v1/images/uploads", files={"file": ...})
    last_frame_url = resp.json()["url"]
except:
    # Tier 2: imgbb
    if IMGBB_API_KEY:
        b64 = base64.b64encode(open(last_frame_path, "rb").read()).decode()
        resp = httpx.post("https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64}, timeout=15)
        last_frame_url = resp.json()["data"]["url"]
    else:
        last_frame_url = None  # Tier 3: prompt only
```

### 輸出記錄

`video_jobs.json` 中每場景新增 `frame_chaining_url` 欄位：

```json
{
  "scene_id": 1,
  "frame_chaining": true,
  "frame_chaining_url": "https://i.ibb.co/xxx/last-frame.jpg",
  "frame_chaining_tier": "imgbb",
  "status": "completed",
  "output_url": "https://..."
}
```

- `frame_chaining: true` → 有真實圖片錨點傳入 end_image
- `frame_chaining_url` → 實際末幀圖片 URL（可直接開啟確認）
- `frame_chaining_tier` → 哪一層上傳成功的（agnes / imgbb / none）

## 與 media-pipeline 的區別

| 面向 | media-pipeline (pipeline-feg.py) | CineAgent (run_pipeline.py) |
|:----|:-------------------------------|:---------------------------|
| 腳本階段 | 無（需手動建立 JSON） | 完整 Phase 0（需求→節奏表→腳本→分鏡→審查） |
| 斷點續傳 | 每次從頭跑 | 基於 `agents_workflow_state.json` 斷點續傳 |
| Frame Chaining | ❌ 無 | ✅ v3.3: ffmpeg 抽末幀 + 3 層上傳 |
| Quality 參數 | ❌ 無 | ✅ `--quality fast/balanced/cinematic` |
| 輸出格式 | pipeline_{run_id}.json | video_jobs.json + image_jobs.json + notify_payload.json |
| LLM 角色 | 無 | 用 agnes-2.0-flash 生成腳本 + coherence pass |

## Quality Presets

三段品質控制透過 `guidance_scale` 和 `motion_bucket_id` 達成：

| Profile | guidance_scale | motion_bucket_id | 效果 |
|:-------|:--------------|:-----------------|:-----|
| `fast` | 2.5 | 127 | 生成快，角色保留弱，動態多但不穩 |
| `balanced` | 3.5 | 80 | 預設，折衷 |
| `cinematic` | **5.0** | **50** | **貼近圖片錨點、動態少、最穩定** |

- **guidance_scale 越高** → 越貼近輸入圖片的視覺特徵（角色保留越好）
- **motion_bucket_id 越低** → 動態強度越低（畫面越穩定，角色越不會漂移）

## Coherence Pass

在腳本生成後，LLM 以 `temperature=0.1` 審查所有場景的 `character_card` 欄位：

1. 收集所有場景的 `scene_id` + `character_card`
2. 發送給 LLM 比對，找出差異欄位
3. LLM 輸出修補後的 JSON（所有場景的 `character_card` 統一為最完整版本）
4. 若 LLM 失敗，跳過不中斷流程

## 輸出檔案

```
output/
├── image_jobs.json         # 每場景生圖記錄（含 request_body）
├── video_jobs.json          # 每場景影片記錄（含 frame_chaining 欄位）
├── script_package.json      # 完整腳本包（beats + scenes + review_notes）
├── beat_sheet.json          # 節奏表情緒曲線
├── notify_payload.json      # 最終摘要
└── scenes/                  # 圖片與影片暫存
```

## 注意事項

- `AGNES_API_KEY` 需從 `~/.hermes/env/agnes.env` 讀取後 export 到環境變數
- **`IMGBB_API_KEY` 建議設定**（Tier 1 的 Agnes upload endpoint 可能不穩定）
- 腳本設計階段會呼叫 agnes-2.0-flash LLM（非推理模型），會消耗 Agnes 配額
- `--skip-script` 可跳過 LLM 階段，直接從 `scene_prompts.json` 載入
- `--reset` 會刪除 `scene_prompts.json` 和 `agents_workflow_state.json`，與 `--skip-script` 互斥
- 最新版 pull：`cd ~/CineAgent && git pull origin main`
- Duration presets 遵循 8n+1 幀數規則，見 `DURATION_PRESETS` 常數