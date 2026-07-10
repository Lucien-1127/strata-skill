---
name: sd-forge-nsfw
description: "透過本地 SD WebUI Forge 生成 NSFW 圖片，支援 DreamShaper 8 與 Realistic Vision V6"
status: stable
---
# sd-forge-nsfw

## 📖 Description

透過本地 SD WebUI Forge 生成 NSFW 圖片，支援 DreamShaper 8 與 Realistic Vision V6

---

# SD Forge NSFW 圖片生成

## 觸發條件
用戶在 Telegram 提到「生圖」、「NSFW」、「色圖」、「nude」、「/nsfw」、「男娘」、「femboy」等關鍵字時使用。

## 前置檢查
1. 確認 SD Forge 是否在線：`curl -s http://127.0.0.1:7860/sdapi/v1/sd-models`
2. 若不在線，啟動：`cd /c/Users/ysga1/SDWebUI-Forge && source venv/Scripts/activate && python launch.py --api --medvram --port 7860`
   - 等待約 30 秒讓模型載入
3. 列出可用模型，讓用戶選擇（或自動選上次用的模型）

## 可用模型

| 模型 | 風格 | 適合 | 參數差異 |
|------|------|------|---------|
| DreamShaper_8_pruned | 藝術寫實混合，全能型 | 二次元/寫實皆可，風格較軟 | prompt: `masterpiece, best quality` 前綴 |
| Realistic_Vision_V6.0_NV_B1_fp16 | 極致寫真/寫實 | 照片級 NSFW，光影最真 | prompt: `RAW photo` 前綴，需搭配 VAE |

**Realistic Vision V6 使用注意：**
- 需搭配 VAE（已安裝：`vae-ft-mse-840000-ema-pruned.safetensors`）
- SD Forge 會自動偵測 VAE，無需手動指定
- 解析度建議 768x1024（半身）或 512x768（全身）
- Sampler 建議 `DPM++ SDE Karras`（25+ steps）

## 生圖參數

### DreamShaper 8（預設）
```json
{
  "prompt": "masterpiece, best quality, (nsfw:1.3), (naked:1.3), {USER_PROMPT}, (photorealistic:1.3), highly detailed, 8k, cinematic lighting, dslr, detailed skin",
  "negative_prompt": "ugly, deformed, blurry, low quality, bad anatomy, bad hands, extra fingers, watermark, text, signature, monochrome, censored",
  "steps": 25,
  "width": 512,
  "height": 768,
  "cfg_scale": 7,
  "sampler_name": "DPM++ 2M Karras",
  "batch_size": 1
}
```

### Realistic Vision V6（選用）
```json
{
  "prompt": "RAW photo, (nsfw:1.3), (naked:1.4), {USER_PROMPT}, 8k uhd, dslr, soft lighting, high quality, film grain, detailed skin pores, natural skin texture",
  "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime), text, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, UnrealisticDream",
  "steps": 25,
  "width": 768,
  "height": 1024,
  "cfg_scale": 5,
  "sampler_name": "DPM++ SDE Karras",
  "batch_size": 1
}
```

## Prompt 建構規則

- **NSFW 權重起手 `(nsfw:1.3)(naked:1.3)`** — 這個用戶偏好強度較高的初始設定（第一次用 1.2 被說不夠 NSFW）
- 若用戶描述有具體姿勢/場景，保留並強化；若無具體描述，預設：`sensual female nude, erotic pose, bedroom, soft lighting`
- reference 檔案：`nsfw-tags.md`（部位/姿勢/場景/表情/道具完整標籤表）

## 男娘 / Femboy 專區

用戶特定偏好類別。參考 X（Twitter）平台寫實風格。

### 核心關鍵字組合
```
femboy, feminine male, flat chest, smooth skin,
slim waist, wide hips, (thick thighs:1.2), thighhighs,
skirt, makeup, long hair, cute face
```
### Negative prompt 必封鎖
```
masculine body, body hair, beard, muscles, old, wrinkled
```

### Femboy 完整範本（DreamShaper 8）
```
masterpiece, best quality, (nsfw:1.3), (naked:1.3),
femboy, feminine male, flat chest, slim waist, thighhighs,
skirt, cute face, makeup, long hair, {USER_POSE},
soft lighting, (photorealistic:1.3), cinematic, detailed skin
```

### Femboy 完整範本（Realistic Vision V6／X平台風格）
```
RAW photo, (nsfw:1.3), (naked:1.4),
femboy, feminine male, slim waist, flat chest,
{d['USER_POSE']}, thighhighs, skirt,
dslr, soft window lighting, detailed skin pores,
film grain, 8k uhd, natural skin texture
```

### 多重男娘
多位 femboy 時用 `2girls, all femboy` 或 `3girls, all femboy` 標籤。

完整參考：`references/femboy-nsfw.md`

## X（Twitter）平台風格指南

用戶引用 X 平台作為風格參考。關鍵差異：

| 面向 | 一般 NSFW | X 平台風格 |
|------|-----------|-----------|
| 模型 | 不拘 | **RV V6 優先**（寫實感最強） |
| 打光 | soft lighting | `dramatic lighting, high contrast` |
| 解析度 | 512x768 | 768x1024 或 896x896（RV V6 建議） |
| 膚質 | detailed skin | `detailed skin pores, natural skin texture` |
| 構圖 | 多變 | `simple background, centered composition` |
| 濾鏡感 | 無 | `slightly desaturated, film grain` |
| 模型參數 | CFG 7, DS 參數 | CFG 5, DPM++ SDE Karras, 25 steps |

## 獨立專案結構

用戶偏好將 NSFW 生成作為獨立專案管理，不依賴 Single skill workflow：

```
C:\Users\ysga1\nsfw-gen/
├── scripts/
│   ├── generate.py       # CLI 生圖（建議使用）
│   └── switch_model.py   # 模型切換
├── references/
│   ├── nsfw-tags.md      # NSFW 標籤大全
│   └── femboy-nsfw.md    # 男娘專用標籤
└── output/               # 預設生圖輸出目錄
```

腳本支援參數：`--model rv6|ds`、`--steps`、`--width`、`--height`、`--cfg`、`--switch`

## 執行步驟

1. 確認 SD Forge 在線
2. 確認用戶要的內容類別 → 選對應模型
3. 根據類別（一般 NSFW / femboy / X 風格）使用對應 prompt 範本
4. 用專案腳本生圖：
   ```bash
   python /c/Users/ysga1/nsfw-gen/scripts/generate.py "描述" --model rv6
   ```
5. 圖片存於 `nsfw-gen/output/`，用下方格式傳送

## 圖片傳送

- 路徑統一用 **forward slashes**：
  ```
  MEDIA:C:/Users/ysga1/nsfw-gen/output/filename.png
  ```
- 反斜線會導致 Telegram 無法送圖（MEDIA: 解析失敗）

## 已知陷阱

| 問題 | 解法 |
|------|------|
| Connection refused | SD Forge 未啟動 → 啟動它（約30秒） |
| 顯存不足 OOM | 加 `--medvram` 或降低解析度到 448x640 |
| 模型未載入 | 使用 switch_model.py 或重啟 SD Forge |
| 圖片太保守/不夠 NSFW | **這個用戶偏好高權重起手**：`(nsfw:1.3)(naked:1.3)` 起跳，還是不夠就加權到 `(nsfw:1.4)(naked:1.5)` |
| MEDIA: 圖片傳送失敗 | 路徑統一用 **forward slashes**：`MEDIA:C:/Users/.../file.png`，不要用反斜線 |
| 用戶說「像X平台風格」 | 指更寫實/更露骨的 Twitter NSFW 風格，用 RV V6 模型 + RAW photo + high contrast |
| RV V6 出圖奇怪 | 檢查 VAE 是否有載入；降低 CFG 到 5；解析度不要低於 512 |
| 用戶說「男娘」但出圖太壯 | 確認 negative prompt 有封鎖 `masculine body, body hair, beard, muscles` |
