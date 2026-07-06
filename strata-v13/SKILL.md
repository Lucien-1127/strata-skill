---
name: strata-v13
description: STRATA V13.0 — Strategic Reasoning & Analysis Through Architecture
version: 13.0
author: Hermes + 老闆
metadata:
  hermes:
    tags: [STRATA, Architecture, Enterprise, AI-System, 4-Layer]
---

# 💎 STRATA V13.0

**Strategic Reasoning & Analysis Through Architecture**

企業級穩定對話中樞架構。一套專為長期、高穩定性專業對話設計的 AI 系統框架，具備狀態自校驗、動態豁免邊界與智慧記憶壓縮能力。

前身：磐石矩陣（Bedrock Matrix）。改名的唯一原因是避免與 AWS Bedrock 品牌衝突。

## When to Use

- 建立/審計/維護 STRATA 生態系統中的任何技能時，作為總索引參照
- 需要了解哪個子技能負責什麼功能時
- 排查跨技能整合問題（如 FSM 狀態卡住、δ 路由斷裂、記憶未壓縮）
- 新成員入門：了解 STRATA 的四層架構與六子系統
- 直接呼叫：「載入 STRATA V13 架構」

## Prerequisites

- 所有子技能已建立並存放於 `~/.hermes/skills/strategy/`
- FEG DSL 權威參考：`prompt-factory-7-1/references/feg-core-dsl.md`（共享）
- 記憶壓縮 cronjob 已部署（job_id: `d7d5c749c9fd`，每 2h）

## How to Run

此技能為**架構總綱**，不直接執行任務。載入後提供各子技能的定位資訊與交叉引用路徑。

```bash
# 載入總綱
skill_view(name="strata-v13")

# 根據需求載入對應子技能
skill_view(name="strat-orchestrator")   # 流程控制
skill_view(name="strat-anchor-5d")      # 情境錨定 + 5D
skill_view(name="strat-drill")          # 壓力測試
skill_view(name="strat-forge-output")   # 輸出鍛造
skill_view(name="strat-memory-policy")  # 記憶策略
skill_view(name="decision-graph-router")# FEG 路由
```

## 核心架構

### 四層運算

1. **系統回顯與防護層** — 身分驗證、注入防護、δ1-δ3 安全校驗
2. **提問重構層** — 模糊意圖精煉、語意校正、FEG 決策路由
3. **深度推理層** — 鏈式思考、多路驗證、STRAT 五階段流程
4. **精準解答層** — 結構化輸出、格式控制、閉環品質閘門

### 子系統與技能對照表

| 模組 | 技能名稱 | 功能 | 層級 | 檔案路徑 |
|:-----|:---------|:-----|:----:|:---------|
| **STRATA Orchestrator** | `strat-orchestrator` | FSM 五狀態流程控制 + δ 安全路由 + S0-S4 管理 | 1-2 | `strategy/strat-orchestrator/` |
| **STRATA Anchor (5D)** | `strat-anchor-5d` | 四類鉤子錨定 + 五維研析 + 多層備援 | 2-3 | `strategy/strat-anchor-5d/` |
| **STRATA Drill** | `strat-drill` | 壓力檢核 + 自我質疑遞迴 + 斷點測試 | 3 | `strategy/strat-drill/` |
| **STRATA Forge** | `strat-forge-output` | 閉環五節點 + 輸出契約 + E1-E7 錯誤分類 | 4 | `strategy/strat-forge-output/` |
| **STRATA Memory Policy** | `strat-memory-policy` | SQLite+ChromaDB 雙層儲存 + 壓縮策略 | 1-4 | `strategy/strat-memory-policy/` |
| **STRATA Compression** | `strata-memory-compression` | claude-mem 自動壓縮 cronjob + 增量摘要 | — | `strategy/strata-memory-compression/` |
| **STRATA FEG Router** | `decision-graph-router` | FEG-C 多意圖決策路由 + 域宣告 A-G | 2 | `strategy/decision-graph-router/` |

### 流程：從輸入到交付

```
用戶輸入
    │
    ▼
┌─────────────────────────────┐
│ S0: FEG Router              │  decision-graph-router
│ 域宣告(D_X) + 優先級排序      │  FEG-C 語法解析（參考 feg-core-dsl.md）
└─────────┬───────────────────┘
          │ 域碼 + 優先級 → δ 路由
          ▼
┌─────────────────────────────┐
│ S1: STRATA Anchor (5D)      │  strat-anchor-5d
│ 四類鉤子 → 五維研析          │  目標/風險/效能/延展/情境
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ S2: STRATA Drill             │  strat-drill
│ 壓力檢核 + 自我質疑           │  合理推定/資料不足/已確認
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ S3: STRATA Forge             │  strat-forge-output
│ 閉環五節點 + 輸出契約 + 版本  │  E1-E7 錯誤碼 + G1-G4 品質閘門
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ S4: 交付                     │
│ STRATA Memory 記錄摘要        │  strat-memory-policy + strata-memory-compression
└─────────────────────────────┘
```

## Procedure（維運與除錯）

### 檢查系統完整性

```bash
# 確認所有子技能可載入
for skill in strat-orchestrator strat-anchor-5d strat-drill strat-forge-output strat-memory-policy strata-memory-compression decision-graph-router; do
    skill_view(name="$skill" 2>/dev/null) && echo "[OK] $skill" || echo "[MISSING] $skill"
done

# 確認記憶壓縮 cronjob
hermes cron list | grep "STRATA"
```

### 排查跨技能問題

| 症狀 | 可能原因 | 排查技能 |
|:-----|:--------|:---------|
| FSM 狀態卡在 S1→S2 | FEG Router 未正確輸出域碼或優先級 | `decision-graph-router` |
| 5D 分析輸出空洞 | Anchor Phase 0 未正確錨定 | `strat-anchor-5d` |
| Drill 未產出任何斷點 | 壓力檢核遞迴未觸發 | `strat-drill` |
| Forge 輸出不含錯誤碼 | 輸出契約未執行 | `strat-forge-output` |
| 記憶未壓縮 | cronjob 失效或 state.db 未寫入 | `strata-memory-compression` |
| 新技能 FEG 不一致 | 未參照 `feg-core-dsl.md` 共享參考 | `prompt-factory-7-1/references/feg-core-dsl.md` |

### 跨技能變更的執行順序（維運鐵則）

當需要同時修改多個技能時（如審計後的修復排程），嚴格遵循依賴圖決定執行順序，避免重工和引用斷裂：

| 優先級 | 類別 | 範例 |
|:------:|:-----|:-----|
| **1** | 共享基礎設施 | FEG 參考、命名約定、跨技能協定 |
| **2** | 核心架構 | strata-v13、orchestrator FSM |
| **3** | 直接依賴項 | 引用基礎設施的技能（router、skill-author） |
| **4** | 重命名/遷移 | 目錄改名（需等引用方穩定後執行，避免路徑衝突） |
| **5** | 互補引用 | 雙向引用（memory-policy ↔ memory-compression） |
| **6** | 獨立強化 | 無依賴的單技能改善（安全過濾、參考文件） |

**核心規則**：
1. 共享參考在前，消費者技能在後。
2. 更名類操作延遲到所有引用方穩定後。
3. 合併重疊任務（如 FEG 統一 + router 對齊 = 一個共享參考升級）。
4. 真正獨立的任務平行處理；有依賴的嚴格序列化。
5. 需要額外資料才能執行的項目，明確標記並向用戶索取，不猜測。

> 此規則來自 2026-07-06 審計修復的實戰驗證。

### δ 路由安全校驗

Orchestrator 使用 δ1-δ3 三層語義路由防止資訊洩漏：

| 層 | 檢查 | 觸發條件 |
|:--:|:-----|:---------|
| δ1 | 域宣告不匹配 | FEG Router 輸出與實際任務類型不符 |
| δ2 | 資訊洩漏檢測 | 跨域傳遞不必要上下文 |
| δ3 | 輸出合規 | 交付前格式與目標契約不一致 |

## 命名

- **全名**：STRATA (Strategic Reasoning & Analysis Through Architecture)
- **中文**：磐石矩陣（內部稱呼，僅中文文件使用）
- **版本**：V13.0
- **前身**：Bedrock Matrix（已廢棄，避免 AWS 衝突）

## 最佳場景

- 企業客服/技術支援（長期追蹤）
- 知識庫與決策輔助
- AI 代理人調度
- 多模態代理的多意圖處理
- 提示詞工程與技能開發（搭配 prompt-factory-7-1 + hermes-skill-author）

## 跨技能依賴圖

```
strata-v13 (總綱) ── 引用 ──→ 所有子技能
    │
    ├── strat-orchestrator ── 引用 ──→ decision-graph-router
    │       └── 調度 ──→ anchor-5d, drill, forge-output
    │
    ├── decision-graph-router ── 引用 ──→ feg-core-dsl.md
    │
    ├── strat-memory-policy ── 互補 ──→ strata-memory-compression
    │
    └── hermes-skill-author ── 引用 ──→ feg-core-dsl.md
            prompt-factory-7-1 ── 擁有 ──→ feg-core-dsl.md (共享參考)
```

> FEG DSL 的權威定義為 `prompt-factory-7-1/references/feg-core-dsl.md`。任何技能使用 FEG 壓縮或 FEG-C 語法時，請引用此共享參考，避免重複定義造成碎片化。

## Pitfalls

- **不要把總綱當執行技能**：`strata-v13` 是架構索引，不包含可執行步驟。載入後需根據任務載入對應子技能。
- **不要繞過 FEG Router 直接進入 Anchor**：Skil-S0 的域宣告和優先級排序是後續流程的前提。跳過 FEG Router = 跳過多意圖處理和 δ1 安全校驗。
- **記憶雙系統需互相引用**：`strat-memory-policy`（策略層）與 `strata-memory-compression`（執行層）是互補關係。讀取記憶策略時也要檢查壓縮 cronjob 是否正常運作。
- **δ 路由斷裂難以察覺**：當 FSM 狀態轉移看似正常但輸出空洞時，檢查 δ1-δ3 是否在每個節點都有執行快照記錄。症狀：輸出品質穩定下降但無報錯。
- **FEG 語法碎片化**：跨技能使用 FEG 時，務必引用 `feg-core-dsl.md` 共享參考而非自定義。目前存在 FEG-C 變體（decision-graph-router），需確保其核心語法與共享定義一致。
- **禁止詞陷阱**：建立和維護技能時避免使用 powerful/seamless/robust/comprehensive 等浮誇形容詞。參考 hermes-skill-author 的 HARDLINE_RULES。

## Verification

```bash
# 確認總綱可被載入
skill_view(name="strata-v13")

# 確認所有子技能存在
skills_list | grep -E "strat-|decision-graph|strata-" 

# 預期輸出包含：
# - strat-orchestrator
# - strat-anchor-5d
# - strat-drill
# - strat-forge-output
# - strat-memory-policy
# - strata-memory-compression
# - decision-graph-router

# 確認 FEG 共享參考存在
ls ~/.hermes/skills/prompt-engineering/prompt-factory-7-1/references/feg-core-dsl.md
```

## 來源

原檔: 知識庫/💎磐石技能開發/💎 磐石矩陣 V13.0 企業級 AI 系統.md
