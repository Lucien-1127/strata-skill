---
name: strat-forge-output
description: Forge final output plus format specifications.
version: 0.1.1
author: Hermes
metadata:
  hermes:
    tags: [Strategy, Forge, Output, Format, Specification]
---

# 🔨 Forge + Output Spec 最終鍛造與輸出規範

接收 Anchor+5D 的分析結論與 Drill 的風險燈號，鍛造為最終輸出。同時管理所有輸出的格式規範，確保 Markdown 代碼塊、條列、表格、繁體中文、風險燈號、信心標記的一致性。

## When to Use

- 由 `strat-orchestrator` 在 Anchor+5D + Drill 完成後呼叫
- 需要產出結構化的最終報告/方案
- 需要確保輸出格式一致性
- 直接呼叫：「進行鍛造輸出」

## Prerequisites

- `strat-anchor-5d` 已完成（錨定 + 五維分數）
- `strat-drill` 已完成（壓力檢核 + 燈號）
- `strat-orchestrator` 已提供任務分類

## Procedure

### Phase 0 — 閉環架構總覽

Forge 是 STRAT 系統閉環的樞紐節點。它不只接收並組裝，更將 Drill 的檢核結果反向饋入輸出契約。閉環共有五節點：

```
輸入定義 → 執行層 → 評估層 → 修正層 → 再部署層
    ↑                                        │
    └──────────── 回饋閉環 ──────────────────┘
```

> 關鍵原則：**回饋必須能反向改變系統行為，否則只是監控。** Forge 的每次輸出都是下次輸入的基準線 — 輸出契約中包含版本號、評估分數、修正記錄，供下次 Forge 時對照。

#### 三層閉環對應

| 層級 | 範圍 | 閉環行為 | 對應 Forge 元件 |
|:----:|:------|:---------|:---------------|
| **提示層** | wording、結構、few-shot | 輸出評估 → 調整模板 | Output Spec 品質閘門 |
| **流程層** | 步驟拆分、模組順序、重試 | Drill → 修正 → 再產出 | Phase 3 鍛造流程 |
| **治理層** | 版本、變更原因、回歸測試 | 變更記錄 → 版本追蹤 | S4 版本治理 |

### Phase 1 — 接收輸入

從前述模組收集：
- Anchor 摘要（1-2 句）
- 5D 評分表
- Drill 燈號（🟢/🟡/🔴）
- Orchestrator 任務分類

### Phase 2 — 格式套用（Output Spec）

#### 通用格式規範（所有輸出適用）

```
1. 結論先行 — 第一句就是答案
2. 風險燈號標記 — 🟢/🟡/🔴 在結論旁
3. 信心標記 — 不確定處標註信心百分比
4. Markdown 結構化 — ### 分節、| 表格、- 條列
5. 台灣繁體中文
6. 可複製 — 程式碼區塊、表格可直接複用
```

#### 信心標記規則（源自 Ver.4.0）

| 信心 | 標記 | 適用 |
|:----:|:----:|:------|
| ≥90% | 無需標記 | 直接從明確來源推導 |
| 70-89% | `（基於合理推論）` | 有依據但非直接確認 |
| 50-69% | `⚠️ 需驗證` | 猜測或類比 |
| <50% | `🔴 資料不足` | 無足夠資訊 |

#### 品質閘門（產出前自檢）

| 閘門 | 檢查 | 通過條件 |
|:----:|:-----|:---------|
| G1 結論先行 | 第一句是否為核心答案 | 非背景介紹或假設 |
| G2 燈號存在 | 有無 🟢/🟡/🔴 標記 | 至少一個明確燈號 |
| G3 信心標記 | 不確定處有無標記 | 推論處有（推論）或 ⚠️ |
| G4 可複製 | 程式碼/指令有無格式化 | 所有命令在 code block 內 |

### Phase 3 — 鍛造輸出

依據任務類型選擇輸出結構：

#### 分析/比較型

```
## 🟢/🟡/🔴 結論：{一句話答案}

### 分析架構
{簡要背景}

### 關鍵發現（依 5D 排序）
| 維度 | 分數 | 摘要 |
|:----|:----:|:------|
| 目標 | X/5 | ... |

### 風險與對策
{Drill 燈號 + 對應緩解}

### 建議行動
1. {可執行步驟}
2. ...
```

#### 生成/規劃型

```
## 🟢/🟡/🔴 方案：{方案名稱}

### 概述
{一頁摘要}

### 執行路徑
1. {步驟一}
2. {步驟二}
...

### 資源需求
{所需資源}

### 成功指標
{如何衡量}
```

#### 重寫/優化型

```
## 🟢/🟡/🔴 優化版本 v{version}

### 變更摘要
{改了什麼 + 為什麼}

### 優化後內容
```{格式}
...
```

### [v1→v2] 變更記錄（若有多版本）
- 變更 1: ...
```

### Phase 4 — 交付模式（僅當用戶說「請交付」時觸發）

交付物最低標準：
1. **行動清單**：3-7 項具體步驟（含負責角色、時程）
2. **決策備忘錄**：≥2 關鍵決策點（含利弊與推薦）
3. **實用資產**：一個可直接使用或修改的實例

### Phase 5 — 輸出契約（Output Contract）

每次 Forge 必須產出一份機器可讀的輸出契約，定義輸出應滿足的結構、格式、品質門檻。契約在 S3 品質驗證階段回讀，決定 PASS/FAIL。

```yaml
# output-contract.yaml
contract_version: "1.0"
task_id: "{uuid}"
task_type: "分析"           # 分析/生成/重寫/規劃

structure:
  required_sections:
    - 結論
    - 關鍵發現
    - 風險與對策
    - 建議行動
  optional_sections:
    - 背景補充
  prohibited_patterns:
    - "根據我的分析"          # 水話
    - "總而言之"              # 重複結論
    - 無來源的絕對斷言

format:
  max_total_lines: 200
  table_min_rows: 2
  code_block_required: false   # 分析型任務通常 false

quality_gates:
  G1_conclusion_first: true
  G2_light_exists: true
  G3_confidence_marked: true
  G4_copyable_output: false     # 分析型 < 生成型

fallback:                       # 失敗時的降級輸出格式
  format: "plain_text"
  message: "部分分析完成。以下為已知限制與初步發現。"
```

#### 雙軌評估（Rule + Semantic）

| 評估模式 | 檢查方式 | 適用 | 範例 |
|:---------|:---------|:-----|:-----|
| **規則型** | Regex、JSON schema 驗證 | 格式、結構、欄位完整性 | 必填欄位是否存在 |
| **語義型** | 輔助 LLM 評估 | 邏輯一致性、結論品質 | 「結論是否與分析一致？」 |

規則型先行（快速、零成本），語義型後補（只在規則型 PASS 時觸發）。

### Phase 6 — 錯誤分類法（Error Taxonomy）

當 S3 品質驗證退回重做時，使用以下分類標記錯誤類型，讓修正層有目標地修復：

| 錯誤碼 | 類型 | 現象 | 修正方向 |
|:------:|:-----|:-----|:---------|
| **E1** | 格式錯誤 | 輸出格式不符合 Output Spec | 套用正確模板 |
| **E2** | 任務理解偏差 | 解決了錯誤的問題 | 回 Anchor 重新錨定 |
| **E3** | 上下文不足 | 結論超越已知資訊範圍 | 標記信心 + 新增缺口 |
| **E4** | 過度推論 | 推測寫成事實 | 加上 ⚠️ 或 🔴 標記 |
| **E5** | 違反限制 | 輸出包含禁止內容 | 過濾 + 重新套用模板 |
| **E6** | 漏答欄位 | 部分必填欄位空白 | 補填或標記 N/A |
| **E7** | 交接失真 | Anchor→Drill→Forge 之間資訊遺失 | 回驗 Anchor 狀態快照，重新錨定 |

> E7 是最難發現的錯誤。資訊在模組間傳遞時可能被簡化、扭曲或遺漏。解決方案：每個模組的輸出嵌入原始輸入摘要，供下一個模組對照。

### Phase 7 — 版本治理（Version Governance）

每次產出變更時，須版本化的元件：

| 編號 | 元件 | 版本化內容 | 格式 |
|:----:|:-----|:-----------|:-----|
| V1 | Prompt 本體 | 模板 wording 變更 | `v{major}.{minor}` |
| V2 | 任務模板 | 結構/章節變更 | `v{major}.{minor}` |
| V3 | 模型版本 | 產出此版本的模型 ID | `{model}:{date}` |
| V4 | 參數設定 | temperature/top_p/max_tokens | JSON |
| V5 | 評估規則 | 品質閘門變更 | `v{major}.{minor}` |
| V6 | Few-shot 版本 | 範例內容變更 | `v{major}.{minor}` |
| V7 | 路由配置 | 模組順序/跳過規則變更 | YAML diff |

#### 提示詞變更記錄 (Changelog)

```markdown
## Prompt Changelog

| 版本 | 日期 | 變更 | 原因 | 影響 |
|:-----|:-----|:-----|:-----|:-----|
| v1.0 | 2026-03-21 | 初版 | 首次部署 | — |
| v1.1 | 2026-04-10 | 新增 E6 錯誤碼 | 頻繁出現漏答欄位 | 修正層新增欄位補填 |
| v2.0 | 2026-06-15 | 重構 Phase 2 格式規範 | 增加雙軌評估 | 所有輸出須通過規則型+語義型 |
```

### Phase 8 — YAML 管線配置（部署用）

將閉環五節點映射為可執行的 YAML 設定：

```yaml
pipeline:
  name: "zhiyan-legal-forge-pipeline"
  version: "1.0"
  
  stages:
    - id: "input_definition"
      type: "collect"
      sources: ["anchor", "5d", "drill"]
      
    - id: "execution"
      type: "forge"
      template: "analysis"  # analysis | generation | rewrite
      
    - id: "evaluation"
      type: "validate"
      checks:
        - type: "rule"
          spec: "output_contract.yaml"
        - type: "semantic"
          model: "deepseek-v4-pro"
          
    - id: "correction"
      type: "retry"
      max_attempts: 2
      error_map:
        E1: "reformat"           # 格式錯誤 → 套用正確模板
        E2: "reanchor"           # 任務理解偏差 → 回 Anchor 重新錨定
        E3: "amend_and_remark"   # 上下文不足 → 標記信心 + 新增缺口
        E4: "amend_and_remark"   # 過度推論 → 加上 ⚠️ 或 🔴 標記
        E5: "reformat"           # 違反限制 → 過濾 + 重新套用模板
        E6: "amend_and_remark"   # 漏答欄位 → 補填或標記 N/A
        E7: "reanchor"           # 交接失真 → 回驗 Anchor 快照，重新錨定
        
    - id: "redeploy"
      type: "deliver"
      version_bump: "auto"
      changelog: true
```

## Pitfalls

- **Forge 不做新分析**：所有分析已在 Anchor+5D+Drill 完成。Forge 只負責組織與呈現。
- **格式統一優先於創意**：所有輸出必須通過 Output Spec 品質閘門。創意表現在內容深度而非格式變化。
- **信心標記不可遺漏**：推論處沒標記比推論錯誤更嚴重 — 前者誤導，後者可校正。
- **交付模式不可主動觸發**：只有當用戶明確說「請交付」或「請給最終版本」時才產出交付物。
- **E7 交接失真**：模組間傳遞資訊時，只傳結論不傳前提。每個模組的輸出應嵌入 1-2 句原始輸入摘要，讓下一模組可對照。E7 修正方向是 reanchor（退回 Anchor 對照快照），不是 amend_and_remark。
- **E5 違反限制**：此類錯誤根因是輸出格式或內容不符規範，修正方向是 reformat（重新套用模板過濾），不是語義層的 amend_and_remark。
- **契約過度約束**：Output Contract 的 `prohibited_patterns` 和 `required_sections` 應根據任務類型動態調整。分析型禁用某些水話是合理的；創意型過度約束反而扼殺產出。
- **評估模式錯配**：語義型評估應只用於邏輯一致性檢查，不應用於格式檢查。格式檢查永遠是規則型的職責。
- **版本爆炸**：七項元件都版本化聽起來完整，但實務上每次輸出都版本化太重。只記錄「實際改變的元件」的版本 — V1-V7 是選單，不是清單。

## Verification

```python
# 確認輸出包含：
# 1. 結論先行（第一句是答案）
# 2. 🟢/🟡/🔴 燈號
# 3. 信心標記（推論處）
# 4. 符合任務類型的輸出結構
```
