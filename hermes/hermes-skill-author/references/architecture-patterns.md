# 技能架構三模式：FEG / State Machine / Hook

每份 SKILL.md 可以（也應該）包含這三種模式的痕跡。不是每個技能都要三種全用，但理解它們如何映射到技能結構，能讓技能更強健、更可預測。

---

## 1. Hook（攔截點）→ Prerequisites / Pitfalls / Verification

Hook 是在特定事件發生時插入的邏輯檢查。在技能中，Hook 散佈在三個區塊：

| 技能區塊 | Hook 角色 | 範例 |
|---|---|---|
| `## Prerequisites` | 前置檢查 | 「如果沒有裝 nvm，先安裝」 |
| `## Pitfalls` | 防呆攔截 | 「tsc 通過不代表 API 接好」 |
| `## Verification` | 事後驗證 | 「curl 真實端點確認 schema」 |

Hook 的特性：
- **輕量** — 不需要流程控制，一句話就能攔住錯誤
- **防呆** — 把之前犯過的錯變成文字規則
- **累積式** — 每次犯新錯就往 Pitfalls 加一條

**實作原則**：驗證發現的每個已知模式錯誤，都必須在緊接著的回合更新相關技能的 Hook 區塊。這是技能自我進化的最小閉環。

---

## 2. State Machine（狀態機）→ Procedure 分段

技能的操作步驟本身就是一個隱式的狀態機：

```
idle → ready → running → verified → done
                  ↓
              rollback → idle
```

每個步驟都是一個狀態轉換：

| Procedure 步驟 | 進入條件 | 產出 | 下個步驟 |
|---|---|---|---|
| 1. 檢查前置 | 無（技能啟動） | 環境就緒 / 錯誤訊息 | → step 2 或退回 idle |
| 2. 執行主要邏輯 | 前置通過 | 產出檔案 / API 回應 | → step 3 |
| 3. 自我驗證 | 執行成功 | 驗證通過 / 驗證失敗 | → step 4 或退回 step 2 |
| 4. 清理與回報 | 驗證通過 | 完成狀態 | → done |

**何時需要正規化為狀態機**：當 Procedure 有兩個以上條件分支時（例如 step 2 成功走 A、失敗走 B），就應該在技能中明確寫出分支條件：

```
## Procedure
1. 檢查金鑰 → 無金鑰則提示用戶，中止
2. 測試連線 → 失敗則重試 2 次，仍失敗則走離線模式
3. 執行主要操作
4. 驗證結果
```

---

## 3. FEG（有限執行圖）→ 跨技能調度

FEG 描述的是**整個工作流程圖**，不是單一步驟。

在技能中，FEG 出現在兩個層次：

### 層次 A：技能內部的 FEG（Procedure + 條件跳轉）

當 Procedure 有 3+ 個條件分支時，用 FEG 可視化：

```
  ┌→ A 路徑：step 2a → step 3a → done
  │
開始 → step 1 → 判斷條件 ─→ B 路徑：step 2b → step 3b → done
                          │
                          └→ C 路徑：step 2c → step 3c → done
```

### 層次 B：跨技能的 FEG（多技能組合）

當一個任務需要調用多個技能時，用 FEG 描述調度關係：

```
用戶請求
  → [routing-skill] 判斷走哪個 provider
      → A 分支：[generate-image] → [qc-skill] → [output]
      → B 分支：[reasoning-skill] → [format-skill] → [output]
```

在 Hermes 中，跨技能 FEG 透過 `delegate_task` + `skill_load` 實現。

---

## 實戰範例：API 儀表板開發的架構映射

以本會話中建立的 API 服務狀態頁面為例：

| 模式 | 對應位置 | 內容 |
|---|---|---|
| **Hook** | `docker-check.sh` 腳本 | 啟動前檢查 port 是否被占用 |
| **Hook** | Verification 章節 | 「curl 確認 8 項 KPI 是否全回傳」 |
| **State** | Procedure 步驟 2-4 | loading → data_fetched → error/渲染 |
| **FEG** | 跨技能 | `api-status-skill` → `nginx-config-skill` → `tunnel-skill` |

---

## 驗證清單

撰寫或更新技能時，檢查以下問題：

- [ ] 有 Hook 嗎？（Prerequisites / Pitfalls / Verification 是否涵蓋已知錯誤模式？）
- [ ] 有 State Machine 嗎？（Procedure 分支條件是否有明確寫出？）
- [ ] 有 FEG 嗎？（多技能協作時是否有調度圖？）
