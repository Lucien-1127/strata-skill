# CineAgent 高連貫性優質影片策略指南

> 善用寫作框架與視覺鎖定機制 — 避免 AI 前後不一或流於流水帳

## 1. 角色卡 (character_card) 設定

角色卡是達成影片一致性的核心。透過明確定義角色的外觀特徵，AI 在生成不同分鏡時，主角形象不會發生劇烈變動。

### 鎖定五大關鍵特徵

| # | 面向 | 範例 |
|:--|:-----|:-----|
| 1 | 性別與年齡 | `25歲男性` |
| 2 | 髮型與髮色 | `金色短髮`、`高馬尾` |
| 3 | 服裝細節 | `白色襯衫搭配黑色西裝褲` — 避免每幕換衣服 |
| 4 | 面部/身體特徵 | `黑框眼鏡`、`雀斑`、`疤痕` |
| 5 | 獨特標記 | 一個高辨識度特徵作為「視覺鉤子」 |

### 描述原則

> 越具體越好：`一個 25 歲、穿著藍色連帽衫、戴著黑框眼鏡、留著棕色捲髮的男子` ≫ `一個年輕男子`

### 職責分離

| 負責項目 | 放入 | 範例 |
|:-----|:-----|:-----|
| 主角的不變特徵 | **character_card** | `25歲男性, 金色短髮, 藍色連帽衫, 黑框眼鏡` |
| 畫面的全域感官 | **visual_style** | `電影感調色, 霓虹燈光, 膠卷顆粒, 賽博龐克氛圍` |

> ⚠️ 不在 visual_style 中描述角色，不在 character_card 中描述環境

### 系統融合機制

CineAgent 的流水線將 character_card 與 visual_style 作為「全域常數」，在每個分鏡生成時自動融合。例：腳本要求「主角在街上奔跑」→ `[角色卡特徵] 正在 [視覺風格描述] 的街道上奔跑`

---

## 2. 視覺風格 (visual_style) 設定

### 四要素構成

以**逗號分隔關鍵詞**格式撰寫（Agnes Image 2.1 擴散模型最佳理解格式）：

| # | 要素 | 關鍵詞範例 |
|:--|:-----|:-----|
| ① | **藝術類型** | `Cinematic`, `Anime style`, `3D render`, `Cyberpunk`, `Oil painting` |
| ② | **光線設定** | `Soft ambient lighting`, `Volumetric lighting`, `Neon glow`, `Golden hour` |
| ③ | **色調與調色** | `Teal and orange`, `Warm earthy tones`, `Monochrome`, `High saturation` |
| ④ | **鏡頭質感** | `Film grain`, `Deep depth of field`, `Wide angle`, `Anamorphic lens flare` |

### 優質範例 vs 錯誤範例

| | 描述 | 判斷 |
|:--|:-----|:-----|
| ✅ | `Cinematic realism, teal and orange color grading, soft natural sunlight, 8k resolution, highly detailed textures, film grain` | 四要素完備 |
| ✅ | `Cyberpunk aesthetic, neon blue and pink lighting, dark rainy atmosphere, volumetric fog, high contrast, futuristic vibe` | 氛圍明確 |
| ❌ | `Beautiful video` | AI 隨機發揮 → 每幕風格不同 |
| ❌ | `Cinematic, a man running` | 混入角色描述 → 干擾角色卡 |

---

## 3. 故事與節奏的連貫性：注入「敘事靈魂」

優質影片的點閱率取決於前幾秒，留存率取決於節奏。CineAgent 將三個框架協同組成「說故事大腦」：

| 框架 | 作用層級 | 負責 |
|:-----|:-----|:-----|
| **三幕劇結構** | 宏觀 | 技術文件／整體敘事架構（開端、對抗、結局） |
| **Save the Cat 節奏表** | 微觀 | 情緒與節奏點控制（`emotion_curve`） |
| **Hook-Value-CTA** | 分鏡級 | 每一幕的功能定位（吸引→價值→行動） |

### Save the Cat × 情緒曲線 (Emotion Curve)

系統在 **Phase 0 / Step 2: 節奏表設計** 中執行（`run_pipeline.py:581-640`）：

```json
{
  "emotion_curve": "平靜→緊張→高潮→收束",
  "beats": [
    {"beat_id": 1, "name": "Hook",    "time_start": 0,  "time_end": 3,    "purpose": "吸引眼球", "emotion": "好奇", "camera": "特寫"},
    {"beat_id": 2, "name": "展示",     "time_start": 3,  "time_end": 15,   "purpose": "展現主題", "emotion": "興趣", "camera": "中景"},
    {"beat_id": 3, "name": "高潮",     "time_start": 15, "time_end": 25,   "purpose": "情緒頂點", "emotion": "驚嘆", "camera": "動態"},
    {"beat_id": 4, "name": "收尾",     "time_start": 25, "time_end": 30,   "purpose": "收束",     "emotion": "滿足", "camera": "拉遠"}
  ]
}
```

- **Temperature 0.3**（`run_pipeline.py:612`）：低溫確保故事結構嚴謹，不發散
- **每個節拍含**：`name / time / purpose / emotion / camera` — 五維控制
- **容錯設計**：LLM 失敗時自動 fallback 到預設 4 節奏（Hook→展示→高潮→收尾）

### Temperature 分工策略

| 階段 | Temperature | 理由 |
|:-----|:----------:|:-----|
| 節奏表 (Step 2) | **0.3** | 結構必須嚴謹，防止邏輯發散 |
| 腳本/分鏡 (Step 3-4) | **0.7**（預設） | 允許合理創意，生成有驚喜的畫面感 |
| Coherence Pass | **0.1** | 極低溫確保角色卡統一，不創造新版本 |

## 2. 視覺的連貫性：啟動「物理鎖定」

AI 最怕「金髮美女變黑髮大叔」的不一致。CineAgent 的 Consistency Control 解決這問題：

- **嚴格定義 character_card（角色卡）**：性別、年齡、服裝、髮型、面部特徵全部鎖定，跨場景不變
- **跨場景統一 visual_style**：色調（冷/賽博朋克）、光線（逆光/柔光）、美術風格全部統一
- **Coherence Pass**（Step 4.5）：LLM 審查所有場景 character_card 後強制寫回統一版本
- **自動過濾雜訊（負面提示詞）**：系統自動附加 Negative Prompts，排除崩壞/多指/變形

## 3. 技術與參數優化：順應「模型規則」

| 規則 | 說明 |
|:-----|:-----|
| **8n+1 幀規則** | Agnes Video 2.0 的幀數限制，設定鏡頭長度時順應此規律 → 畫面過渡更流暢 |
| **Temperature 調校** | 節奏表 0.3（邏輯嚴謹），分鏡 0.7（創意驚喜），Coherence 0.1（極低溫鎖定） |
| **輕量部署** | GCP e2-micro（每月 ~$6）即可跑動，重度運算走 Agnes API 雲端 |

## 4. 查錯優先級

遇到不連貫問題時，**依序檢查**：

1. ✅ `character_card` 是否有明確定義？→ Coherence Pass 是否執行？
2. ✅ `visual_style` 是否所有場景相同？
3. ✅ `emotion_curve` 是否啟動？節奏表 Temperature 是否為 0.3？
4. ✅ 分鏡 Temperature 是否為 0.7？
5. ✅ Hook-Value-CTA 框架是否套用到每個分鏡？
6. ✅ 版本是否最新（Agnes API 對齊修復）？

## 相關連結

- CineAgent repo: `~/CineAgent/` (v3.3+)
- Agnes API docs: agnes-ai.space
- Frame Chaining: ffmpeg 末幀抽取 + imgbb 上傳
