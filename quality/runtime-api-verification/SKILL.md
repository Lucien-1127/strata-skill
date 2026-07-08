---
name: runtime-api-verification
description: "Foreach API change: curl endpoint then compare types."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [QC, API, Frontend, Verification]
---

# Runtime API Pipeline Verification

> 每次修改前端/API 串接後，**不只檢查 TypeScript 編譯**，必須驗證完整資料管線在 runtime 是否一致。

## When to Use

- 建立或修改前端頁面時（Dashboard、金鑰管理、設定等）
- 子代理建立完整 Component 後，進入 QC 階段時
- 任何從後端取資料的 hook 或 service 層被修改時
- 當使用者抱怨「點了沒反應」「畫面沒東西」「資料不對」時

## Procedure

### 1. 確認後端 API 真實回應格式

```bash
curl -s http://localhost:8081/api/{endpoint} | python3 -m json.tool | head -40
```

### 2. 確認前端型別定義

檢查 `src/types/` 下對應的 TypeScript 型別，確認欄位名稱、型別、巢狀結構。

### 3. 逐一比對

對後端回應的每個頂層 key，在前端型別中找到對應欄位：

- 欄位名稱是否一致？（大小寫、底線/camelCase）
- 型別是否匹配？（string vs number, 巢狀結構深度）
- 可選欄位在後端缺失時，前端是否有容錯？

### 4. 確認資料管線完整

```typescript
後端 API → api client (src/services/api/) 
         → adapter (src/services/adapters/) 
         → hook (src/hooks/) 
         → component (src/pages/ or src/components/)
```

檢查每一層：
- **api client**：endpoint URL、HTTP method、泛型型別參數是否正確
- **adapter**：是否有真正的轉換邏輯？還是只是 `return raw` 的 stub？
- **hook**：是否真的呼叫了 API？還是用 setTimeout 回傳 mock data？
- **component**：是否使用了 hook 的資料？還是用了 inline `const MOCK_KPIS = [...]`？

### 5. 檢查「Mock 汙染」

常見的反覆錯誤模式：

```typescript
// useDashboardData.ts:   用 setTimeout 回傳 createMockPayload()  ← 沒接 API
// DashboardPage.tsx:     第22-217行全是 MOCK_KPIS / MOCK_ALERTS  ← 沒用 hook
// dashboard.api.ts:      endpoint 定義正確但 never called        ← 孤兒程式碼
```

解法：搜尋檔案中所有 `MOCK_` 開頭的常數和 `mock` 字樣，確認是否被真實 API 取代。

## Pitfalls

- **tsc 編譯通過 ≠ 資料串接正確**。Mock data 的型別可以完美對上 UI 元件型別，但後端回傳的可能是完全不同結構的資料。
- **Adapter 是空的**：`adapter.ts` 常被留下 `return raw`，實際上後端格式與前端型別完全不同，根本無法 unmarshal。
- **Hook 用 setTimeout 模擬 API 呼叫**：這讓 tsc 和 build 都通過，但使用者看到的永遠是假資料。
- **Component 直接 inline mock**：即使用 `useDashboardData` hook 定義了，component 自己又有 `MOCK_KPIS` 常數並直接用它渲染，hook 形同虛設。

## Verification

```bash
# 1. 檢查後端回應關鍵欄位
curl -s http://localhost:8081/api/dashboard | python3 -c "import sys,json; d=json.load(sys.stdin); print('KPIS:', len(d['overview']['kpis']), 'keys:', [k['key'] for k in d['overview']['kpis']])"

# 2. 檢查前端是否留下 mock 資料
grep -rn 'MOCK_' src/pages/ src/hooks/ | grep -v 'node_modules'
```
