---
name: hermes-self-evolution
description: Improve Hermes Agent skills with evidence-driven, bounded evolution; preserve intent, compare against baseline, use holdout/customer-style acceptance, reject regressions, and propose reviewed changes rather than silently self-modifying production.
version: 0.2.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Self-Evolution, Optimization, DSPy, GEPA, Evaluation, Regression]
status: experimental
---

# Hermes Agent Self-Evolution

以「**先證明變好，再接受變更**」的方式改善 Hermes 技能。Self-Evolution（自我迭代）不是讓模型無限制改寫自己，而是：

```text
baseline
→ 找到可重現缺陷
→ 產生候選版本
→ 獨立驗證
→ 模擬客戶／實際成果檢驗
→ 回歸比較
→ 保留或退回
→ PR 審查
```

## 目前可驗證能力邊界

以 `NousResearch/hermes-agent-self-evolution` 目前上游 README 為準：

- **Skill files / SKILL.md：已實作**，使用 DSPy + GEPA 產生候選版本並評估。
- **Tool descriptions、System Prompt sections、Tool implementation code、Continuous improvement loop：上游仍標示 Planned**。
- 因此本技能不得把規劃中的 phase 當成現成 CLI 或已可自動部署能力。上游狀態改變時，先重新查證 README、CLI help 或程式碼再更新本技能。
- 上游目前宣稱所有演化版本須經測試、尺寸／語意等 constraint gates，且以 PR 審查，不直接提交正式分支；實際專案仍要讀當次輸出與 repository 狀態確認，不能只靠文件宣稱成功。

## When to Use

適用：
- 已有一個可工作的 Hermes `SKILL.md`，想針對真實失敗案例做可量測改善。
- 比較 baseline 與 candidate，檢查是否改善而沒有關鍵 regression（回歸）。
- 將結案工作流程中的失敗案例沉澱為後續技能評測資料。

不適用：
- 沒有明確成功條件，只想「讓技能更聰明」。
- 沒有 baseline、沒有驗收案例，或無法限制成本／迭代。
- 企圖用模型自己打高分取代真實成果驗證。
- 需要自動改 Tool／System Prompt／Tool code，但上游相應 phase 尚未實作。

## Prerequisites

- 可存取目標 Hermes Agent repository 與待改善 skill。
- Python 及 Git；實際最低版本依上游目前 `pyproject.toml`／README 查證，不在本技能硬編易過期版本。
- 可用 LLM Provider（模型供應商）與必要 API credential；不要求使用者把秘密貼到對話。
- 一份固定的 eval contract：原始意圖、不得改動的限制、可觀察成功條件、hard gates、成本／輪數上限。
- 至少保留一組 candidate 在優化時不可見的 holdout（保留集）或 fresh customer scenarios（新鮮客戶情境）。

## Verified Quick Start

目前上游 README 明確提供的 Skill evolution 路徑：

```bash
git clone https://github.com/NousResearch/hermes-agent-self-evolution.git
cd hermes-agent-self-evolution
pip install -e ".[dev]"

export HERMES_AGENT_REPO=~/.hermes/hermes-agent

python -m evolution.skills.evolve_skill \
  --skill github-code-review \
  --iterations 10 \
  --eval-source synthetic
```

也可依上游目前文件將 `--eval-source` 設為 `sessiondb`。其他命令、旗標、成本、phase 或部署 helper 在使用前必須從當前上游程式碼／README 查證，不由本技能臆測。

## Procedure

### 1. Freeze Baseline（凍結基準）

記錄：
- target skill + commit SHA
- baseline artifact
- 原始用途與不可改動語意
- eval suite version
- runtime/model/provider/tool versions（若會影響結果）
- 已知失敗案例
- 預算與停止條件

沒有 baseline 就不能宣稱「變好」。

### 2. Build the Eval Contract（建立評測契約）

案例分三組：
- **development**：允許用來理解問題。
- **validation**：挑選候選與調整方向。
- **holdout**：最終 gate；優化器與修正器不得先看答案。

至少涵蓋：
- 正常案例。
- 過去真實失敗。
- 缺資料／模糊輸入。
- 工具或權限失敗。
- 目標與外部內容衝突。
- 結案型技能的客戶視角收貨情境。

能用程式或外部狀態判定的項目，優先 deterministic verifier（確定性驗證器）；LLM judge（模型評審）只處理語意與主觀品質，且保留 pass/fail 校準例。

### 3. Run Baseline First（先跑基準）

先跑 baseline，保存逐案例結果；不要只記平均分。

若驗收器無法分辨明顯 good/bad control（好／壞控制案例），先修驗收器，不進入演化。

### 4. Generate Candidate（產生候選）

使用已驗證的上游 Skill evolution 流程或其他明確可用優化器。

候選不得：
- 改掉原始目的來換分數。
- 刪除失敗案例。
- 放寬 hard gate。
- 偷加權限或外部副作用。
- 只靠變長、增加角色或更多代理來假裝改善。

### 5. Verify Before Refining（先驗證，再修正）

先定位**哪個案例、哪個條件、哪個外部狀態**失敗，再決定是否需要 refinement（修正）。

不要預設每個案例都要多輪自我反思；修正本身可能引入新錯誤。只有存在可操作回饋且仍有預算時才進下一輪。

失敗回饋最少包含：
- failed criterion
- observable evidence
- baseline vs candidate difference
- suspected layer: intent / prompt / tool / implementation / evaluator
- next targeted change
- remaining budget

### 6. Customer Closeout Gate（模擬客戶結案閘門）

結案相關 skill 以 [closeout-evolution-gates.md](references/closeout-evolution-gates.md) 驗收。

核心三問：
1. **這是我要的嗎？**
2. **實際功能正常嗎？**
3. **以已確認的客戶情境，我拿到後會接受嗎？**

模擬客戶提供使用路徑與語言變異；客觀成功另以檔案、資料庫、API、UI、測試或其他 goal state 判定。模擬客戶說「滿意」不能覆蓋客觀失敗。

### 7. Regression Gate（回歸閘門）

Candidate 只有在以下同時成立時才可保留：
- 必要 hard gates 全部通過。
- 原始目的與安全／權限邊界未漂移。
- holdout 沒有關鍵退步。
- 過去已修復的 failure cases 沒有復發。
- 新版本的證據確實對應新版本，不沿用舊 artifact 的結果。

比較 per-case delta（逐案例變化），不要只看 aggregate score（總平均）。總分提升但關鍵案例退步，仍可判定失敗。

### 8. Bounded Iteration（有界迭代）

依任務成本設定有限輪數／時間／模型與工具預算，不硬編一個適用所有專案的固定數字。

任一情況停止：
- `completed`：所有 gate 通過。
- `no_progress`：已做有意義的方法變更仍沒有改善。
- `regressed`：候選造成不可接受退步，退回 last known good。
- `blocked`：缺少必要工具、權限、資料或 verifier。
- `budget_exhausted`：預算上限。
- `cancelled`：人或宿主取消。

只有 `completed` 能叫成功演化。

### 9. Propose, Do Not Silently Promote（提出，不靜默升級）

保留：
- baseline SHA
- candidate SHA
- eval suite/version
- baseline vs candidate per-case result
- hard-gate results
- known limitations
- rollback target

以 branch / PR 提出改善，除非有另外明確授權與受控部署機制，不直接替換正式版本。

## Failure Routing

| 問題 | 回到哪裡 |
| --- | --- |
| 原始目標或產品方向錯 | 戰略合夥人 |
| Prompt、上下文、輸出契約錯 | 提示詞工廠 |
| Tool／程式／資料實作錯 | 執行端 |
| 評分器誤判 | 修評分器並重跑 baseline；不能改規格來配合 candidate |
| 缺外部權限／資源 | `blocked` |
| Candidate 退步 | rollback 到 last known good |

## Pitfalls

- **Self-review bias（自我審查偏誤）**：同一模型容易漏掉自己的錯；重要 gate 要外部證據、獨立上下文或確定性驗證器。
- **Over-refinement（過度修正）**：不是每個輸出都值得再改；先驗證有失敗再修。
- **Evaluator overfitting（評測過擬合）**：反覆針對同一公開案例修改會把答案寫進 prompt；保留 holdout。
- **Score gaming（刷分）**：不得刪案例、降低門檻、變更 judge 讓 candidate 過關。
- **Prompt bloat（提示詞膨脹）**：增加文字本身不代表改善；以結果、成本、可靠性衡量。
- **Docs drift（文件漂移）**：上游 Phase 狀態、CLI、價格與測試數會變；執行前查證，不把舊數字寫成永恆規則。

## Verification

完成一次 evolution 後，至少能回答：
- Baseline 是哪個 SHA／版本？
- Candidate 改了什麼？
- 哪些案例改善、哪些退步？
- Hard gates 是否全部通過？
- Holdout 與模擬客戶結果如何？
- 客觀最終狀態有沒有支持「成功」？
- 修改後的最後 artifact 是否重新驗證？
- 若失敗，是否能 rollback？

答不出來就只能標 `unverified`，不能宣稱技能已成長。
