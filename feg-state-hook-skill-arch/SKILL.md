---
name: feg-state-hook-skill-arch
description: "Embed FEG/State/Hook patterns into Hermes skills."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Architecture, FEG, StateMachine, SkillDesign]
status: draft
---

# FEG / State Machine / Hook 技能嵌入架構

> 技能不是說明文件，是邏輯載體。反覆錯的事應在技能層攔截，不靠記憶。

## Core Insight

三種模式不是互斥的選擇，而是**互補的層次**，應直接嵌入技能設計：

```
鉤子 (Hook)         → 事件層：在技能 Prerequisites / Pitfalls / Verification 插入防呆邏輯
狀態機 (State)       → 流程層：Procedure 內的分段步驟 + 條件跳轉 = 狀態轉換圖
FEG (Finite Graph)   → 組合層：多技能 + delegate_task + cronjob 組成完整有向圖
```

## 三模式嵌入技能的方式

### 1. Hook 模式 — 在技能中插入事件攔截

對應技能區塊：**Prerequisites / Pitfalls / Verification**

```markdown
## Prerequisites
- [ ] 前次執行若有錯誤，此步驟強制執行（Hook 攔截重複錯誤）

## Pitfalls
- [必做] deploy 後務必 `curl -s http://localhost:PORT/health`
- 若之前因此出錯過，此步驟由 Verification 強制執行

## Verification
# 單一命令證明技能執行成功
```

**關鍵**：之前犯過的錯，不要只靠記憶避免。直接在技能檔案的 Verification 區塊寫入驗證命令，每次執行時自動觸發。

### 2. State Machine 模式 — 技能步驟即狀態機

對應技能區塊：**Procedure**

```markdown
## Procedure
1. 檢查前置條件     → idle → ready
2. 執行主要邏輯     → ready → running
3. 自我驗證結果     → running → verified
4. 標記完成         → verified → done
5. 失敗回退         → running → rollback → idle
```

狀態轉換表：

| 目前狀態 | 事件 | 下個狀態 | 動作 |
|:--------:|:----:|:--------:|:-----|
| idle | 條件滿足 | ready | 檢查 Prerequisites |
| ready | 開始執行 | running | 執行 Procedure main |
| running | 成功 | verified | 執行自我驗證 |
| verified | 通過 | done | 標記完成 |
| running | 失敗 | rollback | 執行回退動作 |
| rollback | 完成 | idle | 回復初始狀態 |

### 3. FEG 模式 — 多技能組合圖

對應於：**技能間的調度 + delegate_task + cronjob**

每個節點是獨立的技能，邊是條件判斷。用 `delegate_task` 來分派子技能，用 `cronjob` 來觸發週期性節點。

## 設計檢查清單

新技能建立時，問三個問題：

1. **Hook**：之前犯過的相關錯誤，有沒有寫入 Pitfalls / Verification？
2. **State Machine**：Procedure 的每個步驟，是否明確定義了狀態轉換？失敗後的回退路徑在哪？
3. **FEG**：這個技能是終點還是中間節點？與其他技能的組合關係是否在 SKILL.md 中描述了？

## Pitfalls

- **技能不等於記憶**：使用者糾正你的行為後，不要只存到 MEMORY.md，要在相關技能的步驟中寫入防呆邏輯
- **Mock 汙染**：前端技能創建時，子代理容易留下 mock data。FEG 的 verification 節點應包含「檢查 MOCK_ 常數是否被真實 API 取代」
- **狀態機缺少回退路徑**：90% 的技能只定義了快樂路徑（happy path），沒有定義失敗後要怎麼樣。每個狀態轉換都應該有 failure case
