---
name: fastapi-routing-diagnosis
description: FastAPI 後端路由診斷與修復 — 假設驅動、最小修改、迴歸驗證
status: stable
---

# FastAPI 路由診斷

## 📖 Description

結構化診斷 FastAPI 服務的路由層問題：404/502/504 錯誤、路由不存在、middleware 干擾、schema 不匹配。採用「假設驅動診斷法」——先驗證、後修改，每步附強度路由控制 token 消耗。

**When to load**: 使用者回報 API 端點 404、502、504，或要求診斷 FastAPI 路由註冊問題。

## 強度路由

| 等級 | 適用步驟 | 行為 |
|------|---------|------|
| L1 快速 | 偵察、健康檢查、迴歸驗證 | 機械執行，禁止推理鏈 |
| L2 標準 | 單根因修復、diff 撰寫 | 標準推理 |
| L3 深度 | 假設生成排序、跨模組故障、確診失敗後重分析 | 完整推理；窮盡假設空間 |

**升級規則**：同一根因驗證失敗 ≥2 次 → 強制升 L3。L1 中發現異常 → 停止，升 L2 後重判。

## 執行流程

### 1️⃣ 偵察〔L1〕
- curl 各端點健康檢查（含預期 vs 實際 HTTP 狀態碼）
- 讀取 router 定義、middleware 註冊順序、依賴注入
- 輸出實際註冊路由表（對比已知端點清單）

### 2️⃣ 假設〔L3〕
- 列出所有可能根因，按機率排序
- 每項附驗證方法（curl / 單元測試 / 日誌）

### 3️⃣ 驗證〔L2〕
- 逐一以最低成本手段確認根因
- 禁止跳過驗證直接修改

### 4️⃣ 修復〔L2〕
- 最小 diff 修改，不動無關程式碼
- 修改前備份原檔（`cp file.py file.py.bak.$(date +%s)`）

### 5️⃣ 迴歸〔L1〕
- 重跑觸發測試 + 全部端點全掃（含 90 秒長推論逾時場景）

### 6️⃣ 回報〔L1〕
- 根因（一句話）→ 證據 → diff → 驗證結果 → 風險與回滾指令
- 附強度統計表

## 約束

- 禁止未經驗證即修改任何程式碼
- 每次僅修復一個根因；多問題分批處理
- 禁止變更既有端點路徑與回應 schema（前端依賴此契約）
- 無法定位根因時輸出「無法確診」+ 已排除假設清單，禁止臆測性修復
- 強度切換必須符合路由表

## 常見根因分類

| 現象 | 常見根因 | 驗證方式 |
|------|---------|---------|
| 404 | 路由不存在、路徑拼錯、router 未 include | curl + 比對 code 中 route decorator |
| 404 (alias) | 前端呼叫路徑與後端註冊不一致 | 同上 + 確認是否有 alias 路由 |
| 502 | upstream provider 回傳錯誤 | curl provider API 直接測試 |
| 504 | LLM 請求超時（180s+） | 檢查 httpx timeout 設定 |
| Schema error | Pydantic model 欄位不匹配 | curl 帶 payload 確認 422 vs 404 |

## Pitfalls

- **不要用 grep 找路由**：FastAPI 的 `@app.get/post` 裝飾器路徑可能分散在不同 router 檔案中，用 `include_router` 組合。grep 可能遺漏。
- **404 vs 422**：POST payload 格式錯誤通常是 422（Pydantic validation error），不是 404。先確認 HTTP 狀態碼再歸類。
- **靜態檔案掛載可能覆蓋路由**：`app.mount("/static", ...)` 如果 path prefix 與 API 路由衝突，靜態檔案會優先匹配。
- **CORS middleware 順序**：CORS 應在 router 之前註冊（`app.add_middleware` 在上方，`@app.get` 在下方），否則瀏覽器請求會因 preflight 失敗而顯示為 CORS 錯誤而非路由問題。
- **區分「路由不存在」vs「handler 內部拋錯」**：404 可能是路由真的不存在，也可能是 `HTTPException(status_code=404)` 在 handler 內被拋出。後者路由是存在的，只是業務邏輯找不到資源。
- **執行中的版本可能與磁碟不同**：檢查 `/proc/<PID>/cmdline` 確認啟動路徑，並檢查是否有 hot-reload（`--reload` flag）。
