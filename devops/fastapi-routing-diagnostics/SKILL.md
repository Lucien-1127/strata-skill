---
name: fastapi-routing-diagnostics
description: FastAPI 路由診斷與修復 SOP — 假設驅動診斷法，含 L1/L2/L3 思考強度路由
status: stable
---

# FastAPI Routing Diagnostics

## When to Use

當 FastAPI 服務回傳 4xx/5xx、端點 404、或路由設計缺陷需要診斷時載入此技能。遵循「假設驅動診斷法」 — 先驗證、後修改。

## Thinking Strength Routing

每步驟開始前先宣告強度等級：

| 等級 | 適用步驟 | 行為 |
|------|---------|------|
| L1 快速 | 偵察、健康檢查、迴歸驗證 | 機械執行，直出結果，禁止推理鏈 |
| L2 標準 | 單根因修復、diff 撰寫 | 標準推理 |
| L3 深度 | 假設生成排序、跨模組故障、確診失敗後重分析 | 完整推理；窮盡假設空間 |

升級規則：同一根因驗證失敗 ≥2 次 → 強制升 L3。L1 步驟中發現異常 → 停止，升 L2 後重判。禁止在 L1 做根因判斷。

## Procedure

### Step 1: 偵察〔L1〕
- curl 所有已知端點，紀錄 HTTP 狀態碼
- 讀取 FastAPI router 定義（`@app.get/post` 裝飾器）、middleware、依賴注入
- 輸出實際註冊路由表 vs 預期端點對照表

### Step 2: 假設〔L3〕
- 列出所有可能根因，按機率排序
- 每項附驗證方法（curl / 單元測試 / 日誌）
- 至少要包含以下候選項目：
  1. 路由不存在（路徑名稱不符）
  2. FastAPI 路由載入順序問題（middleware 或 static mount 蓋掉）
  3. 請求 schema 不匹配
  4. 執行中的是舊版程式碼（磁碟 vs 進程不一致）

### Step 3: 驗證〔L2〕
- 逐一以最低成本手段驗證
- 第一個驗證確認後即可停止（不浪費 token 驗證全部）

### Step 4: 修復〔L2〕
- 最小 diff 修改，不動無關程式碼
- 修改前備份原檔：`cp server.py server.py.bak.$(date +%s)`
- 禁止變更既有端點路徑與回應 schema（前端 zxFetch 統一層依賴此契約）

### Step 5: 迴歸〔L1〕
- 重跑觸發測試
- 檢查其餘全部端點（含 90 秒長推論逾時場景）

### Step 6: 回報〔L1〕
- Markdown 報告格式：根因(一句話) → 證據 → 修改 diff → 驗證結果(指令 + 實際輸出) → 風險與回滾指令
- 文末附本次各步實際使用強度統計

## Pitfalls

- 無法定位根因時輸出「無法確診」+ 已排除假設清單，禁止臆測性修復
- 修改前務必備份；報告必附回滾指令
- 每次僅修復一個根因；多問題分批處理
- 越級使用 L3 於機械步驟視為違規（浪費 token）
- 路由 alias（redirect 到既有 handler）是最安全的修復方式 — 零邏輯複製，不影響既有端點
