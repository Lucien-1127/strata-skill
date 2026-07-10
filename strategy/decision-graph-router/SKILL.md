---
name: decision-graph-router
description: FEG-style decision routing for multi-modal agents facing ambiguous instructions.
version: 0.1.0
author: Hermes + 老闆
metadata:
  hermes:
    tags: [Strategy, Decision, FEG, Routing, Multi-Agent]
status: stable
---

# 🔀 Decision Graph Router (FEG)

使用 FEG（有限執行圖）語法解決多模態代理面臨模糊多重指令時的混亂問題。與 `strat-orchestrator` 互補：FEG 處理「代理應該做什麼」，strat 處理「代理如何做對」。

## When to Use

- 用戶單次輸入包含多重請求（閒聊 + 翻譯 + 分析混雜）
- 代理無法判斷任務優先級時
- 需要結構化的決策降級路徑
- 直接呼叫：「用 FEG 判斷這個請求」

## Prerequisites

- 已定義決策域目錄（D_ANALYSIS, D_GENERATION, D_REWRITE, D_PLAN 等）
- 或使用 strat-orchestrator 的任務分類作為域目錄

## How to Run

```python
skill_view(name="decision-graph-router")
```

## Procedure

### Phase 0 — 解析輸入為 FEG 語法結構

將使用者輸入映射為 FEG 格式：

```
輸入: "幫我翻譯這段英文，順便問你最近怎麼樣，對了那篇分析寫完了嗎"

FEG 解析:
  D{ D_TRANSLATE | D_CHITCHAT | D_ANALYSIS }
  V: VM_MULTI=3         # 檢測到 3 個意圖
  RULES{
    PRIORITY: D_TRANSLATE > D_ANALYSIS > D_CHITCHAT
    FALLBACK: IF VM_MULTI > 1 → ONE_AT_A_TIME  # 防呆：多意圖逐個處理
  }
  |->
  STATES{
    NORMAL: DONE_ALL
    FALLBACK: PARTIAL_WITH_EXPLANATION
    ABORT: CONFUSION  # 無法判斷時回問用戶
  }
```

### Phase 1 — 域宣告 (D{A..G})

| 域碼 | 決策域 | 觸發條件 | 處理模式 |
|:---:|:-------|:---------|:---------|
| D_A | 分析 (Analysis) | 分析/評估/檢討/風險/審查/判斷 | 完整 STRAT 流程 |
| D_B | 翻譯 (Babel) | 翻譯/中譯/英譯/雙語對照 | Anchor→Forge，跳過 Drill |
| D_C | 對話 (Chat) | 閒聊/問候/心情/壓力/推薦/諮詢 | 快速模式，僅 Anchor |
| D_D | 文件 (Document) | 閱讀/摘要/提取/比對文件 | Anchor→5D（文件專用） |
| D_E | 編輯 (Edit) | 改寫/重寫/潤飾/優化/改一改 | Anchor→Forge（保留原文結構） |
| D_F | 問答 (FAQ) | 定義/解釋/查詢/如何/什麼是 | 直接回答，不經過 STRAT |
| D_G | 生成 (Generate) | 創作/寫作/產生/回信/建議/規劃 | Anchor→Forge，跳過 Drill |

> D_D/E/F 為補充域碼。D_F（問答）是最輕量的域 — 根本不需要進入 STRAT 流程，直接回答即可。D_D（文件）需要前置的文件讀取步驟（read_file），然後才進入 Anchor。D_E（編輯）與 D_G（生成）的邊界：編輯保留原文結構只改寫內容，生成從零開始。

### Phase 2 — 優先級規則 (RULES)

```
RULES{
  # 防呆層：意圖不明時的安全處理
  IF intent_count > 3 → REQUEST_CLARIFICATION
  IF intent_confidence < 0.6 → GUESS_WITH_WARNING

  # 優先級鏈：從高到低
  1. SAFETY_VIOLATION   → ABORT           # 安全違規立即中斷
  2. EXPLICIT_DEADLINE  → FIRST           # 明確時限優先
  3. TASK_COMPLEXITY    → COMPLEX_FIRST   # 複雜任務先處理（佔用認知資源）
  4. USER_ORDER         → AS_STATED       # 用戶自然語言順序

  # 衝突降級
  IF conflict → complex_first THEN explain_ordering
}
```

### Phase 3 — 狀態映射 (STATES)

| 狀態 | 條件 | 行為 | 對應 STRATA FSM |
|:----:|:-----|:-----|:-----------|
| NORMAL | 所有域成功處理 | 輸出完整結果 | S4 交付 |
| PARTIAL | 部分域失敗 | 標記已完成域 + 說明未完成原因 | S3→S4 部分完成 |
| CLARIFY | 無法判斷意圖 | 回問使用者 2-3 個確認問題 | S3 🔴 退回 |
| ABORT | 安全違規/注入 | 拒絕執行 + 記錄事件 | δ1-δ3 🔴 |
| LOOP | 相同糾結 >2 次 | 強制依預設優先級執行 + 標記 | 遞迴收斂 |

## FEG 語法完整參考

本技能使用的 FEG-C 語法是 FEG DSL（定義於 `prompt-factory-7-1/references/feg-core-dsl.md`，共享參考）的特殊化變體，保留核心架構（域宣告→規則→狀態），簡化為適合快速決策路由的格式。

```
FEG{
  D{A|B|C|G}              # 宣告決策域
  V:VM?                    # 可選：虛擬機器模式（單/多域）
}
RULES{
  SAFETY: {禁止事項}
  PRIORITY: {優先級鏈}
  FALLBACK: {降級策略}
}
|->{X}                     # 強制讀取狀態快照
STATES{
  NORMAL: DONE
  FALLBACK: {降級路徑}
  ABORT: {中斷條件}
}
```

## 與 strat-orchestrator 整合

FEG 語法的權威定義位於：**`prompt-factory-7-1/references/feg-core-dsl.md`**（共享參考）。此技能使用 FEG-L2 格式 C（決策圖路由），是標準 FEG DSL 的特殊化變體。

| FEG 做 | strat 做 | 交接格式 |
|:-------|:---------|:---------|
| 解析模糊多意圖 | 單一意圖的深度處理 | FEG 輸出 `任務類型:str` + `域碼:D_X` |
| 決定優先級和順序 | 執行 ANCHOR→5D→DRILL→FORGE | FEG 輸出 `優先級排名` |
| 處理異常/降級/回問 | 輸出品質驗證 (G1-G4) | FEG 輸出 `狀態: NORMAL/PARTIAL/...` |

## Pitfalls

- **域過度分割**：域碼不應超過 7 個（A-G）。每新增一個域就增加一個判斷維度的組合爆炸風險。用 `V:VM?` 標記不確定域，而非為每個模糊情境建立新域碼。
- **優先級剛性**：`RULES{PRIORITY}` 的優先級鏈是預設值，可被用戶明確指令覆蓋。若用戶說「先回答閒聊再翻譯」，不要堅持你的優先級鏈。
- **FEG 不是執行引擎**：FEG 只負責決策路由。解析完交給 strat-orchestrator 或直接處理 — FEG 本身不做內容產生。
- **狀態快照遺漏**：`|->{X}` 語法強制讀取快照，但實務上這個步驟最容易跳過。確保每次狀態轉移前真的有快照可用。

## Verification

```python
# 確認 FEG 輸出包含：
# 1. 域宣告 (D_X: 至少 1 個，最多 7 個)
# 2. 優先級排名 (1,2,3...)
# 3. 狀態標記 (NORMAL/PARTIAL/CLARIFY/ABORT)
# 4. 若有 VM_MULTI > 1，含 FALLBACK 策略
```
