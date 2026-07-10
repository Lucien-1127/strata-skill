---
name: architecture-reimagining
description: 架構重構分析 — 7 步驟系統性設計審查：差距分析、多維探索、替代方案生成、增強建議、模式比對、未來相容、創新審查
status: draft
---

# Architecture Reimagining Protocol

## 📖 Description

在完成任何提示詞、Skill、Agent、Workflow 或 AI 架構分析前，必須先執行「Architecture Reimagining」。目標不是修改文字，而是重新思考整體設計。必須以架構師角度分析目前設計是否仍為最佳方案，而不是假設現有架構正確。

## When to Load

- User 要求對系統/服務/專案進行架構審查
- 使用者抱怨系統不穩定、難以維護或擴充
- 大規模重構前需要方向確認
- 系統有機生長（非刻意設計）後需要結構化檢討

## Protocol

### Step 1: Architecture Gap Analysis

| 檢視維度 | 檢查項目 |
|:---------|:---------|
| 缺少模組 | 是否缺少重要功能模組？ |
| 重複功能 | 是否有重複實作？ |
| 過度設計 | 是否存在不必要的複雜度？ |
| 可抽象化 | 是否有可統一抽象的部分？ |

產出表格：Gap / Severity (P0-P3) / Description

### Step 2: Multi-Dimensional Exploration

至少從下列維度思考。若發現新的維度，允許自行加入。

| 維度 | 問題 |
|:-----|:------|
| Architecture | 整體結構是否合理？ |
| Workflow | 流程是否順暢？ |
| Decision | 決策邏輯集中還是分散？ |
| Validation | 輸入輸出驗證是否完整？ |
| Recovery | 故障恢復機制？ |
| Knowledge | 領域知識如何組織？ |
| Context | 資料上下文一致性？ |
| Memory | 狀態持久化？ |
| Tool Integration | 工具整合方式？ |
| Output Contract | 輸出格式標準？ |
| User Experience | 使用者體驗？ |
| Maintainability | 維護成本？ |
| Extensibility | 擴展能力？ |
| Performance | 效能瓶頸？ |
| Token Efficiency | Token 使用效率？ |
| Cross-Model Compatibility | 跨模型相容性？ |

### Step 3: Alternative Architecture Generation

至少提出三種不同架構：

| 類型 | 說明 |
|:-----|:------|
| **A. Minimal** | 最精簡，最小改動 |
| **B. Balanced** | 推薦方案，最佳平衡 |
| **C. Advanced** | 最高品質，完整解決方案 |

每個方案分析：
- 優點
- 缺點
- 適用情境
- Token 成本（低/中/高）
- 維護成本（低/中/高）
- 擴充能力（低/中/高）

### Step 4: Enhancement Suggestions

除了修正問題，必須主動提出「還可以增加什麼」：

- 新模組
- 新流程
- 新驗證
- 新 Decision Policy
- 新 Workflow
- 新 Plugin
- 新工具整合
- 新 Output Strategy

不得等待使用者提出。每個建議標 Priority (P0-P3)。

### Step 5: Pattern Matching

比對是否符合已知最佳設計模式。若有更好的 Pattern，必須提出替代方案。

表格格式：
| Pattern | Current State | Should Be |
|:--------|:-------------|:-----------|
| Single Responsibility | ❌ 問題描述 | ✅ 建議方案 |
| Strategy Pattern | ... | ... |
| Repository Pattern | ... | ... |
| Circuit Breaker | ... | ... |
| Health Endpoint | ... | ... |
| Graceful Degradation | ... | ... |

### Step 6: Future Compatibility

分析若下列情境發生時，目前架構是否仍適用：

- GPT/Claude/Gemini 新能力加入
- MCP (Model Context Protocol) 整合
- 多用戶支援
- Mobile App (React Native)
- 水平擴展需求

若否，提出新的抽象層設計。

### Step 7: Innovation Review

最後必須回答：

```
目前架構：
□ 只是優化？
□ 還是重新定義？
```

若只是優化，必須再提出至少一個突破性方案。

## Output Format

```markdown
## Architecture Reimagining Report

### 1. Gap Report

| Gap | Severity | Description |
|:----|:--------:|:------------|

### 2. Multi-Dimensional Analysis

| Dimension | Findings |
|:----------|:---------|

### 3. Alternative Architectures

**A. Minimal Architecture**
Pros / Cons / Token Cost / Maintenance / Extensibility

**B. Balanced Architecture (Recommended)**
Pros / Cons / Token Cost / Maintenance / Extensibility

**C. Advanced Architecture**
Pros / Cons / Token Cost / Maintenance / Extensibility

### 4. Enhancement Suggestions

| Enhancement | Priority | Description |
|:------------|:--------:|:------------|

### 5. Pattern Matching

| Pattern | Current | Should Be |
|:--------|:--------|:-----------|

### 6. Future Compatibility

| Scenario | Works? | Changes Needed |
|:---------|:------:|:---------------|

### 7. Innovation Review

**Verdict:** Optimization / Redefinition

### ✅ Final Recommendation

Short-term / Mid-term / Long-term action items.
```

## Relations

- `project-architecture-audit` — 深度程式碼審計（互補：架構 vs 實作）
- `strat-drill` — 壓力測試邏輯與邊界案例（互補：設計 vs 驗證）
- `nginx-spa-basic-auth` — SPA 部署模式（本框架的實踐案例）
