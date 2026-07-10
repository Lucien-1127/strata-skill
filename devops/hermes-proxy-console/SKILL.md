---
name: hermes-proxy-console
description: "TG Mini App dashboard for Hermes Proxy monitoring using native Telegram WebApp API."
version: 0.4.1
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [Telegram, Mini-App, Dashboard, Hermes-Proxy, React, TypeScript]
status: beta
---

# Hermes Proxy Console — Telegram Mini App Dashboard

React + TypeScript Telegram Mini App for monitoring Hermes Agents Proxy on GCP VM.
MVP 版本聚焦行動端，提供 VM/Proxy/Agent 健康度、額度使用狀況、即時告警與關鍵操作。
- 使用原生 `window.Telegram.WebApp` API（不含外部 SDK 套件），深度整合 TG 原生元件。

這個技能是

這個技能是**架構藍圖與任務指引**，定義了檔案樹、型別契約、元件 Props、Api 層組織、TG 原生整合模式與逐步建置優先序。
所有 TypeScript 型別定義與元件 Props 契約存於 `references/` 中，此處只列關鍵摘要。

## When to Use

- 需要從零搭建 Hermes Proxy 的監控 Dashboard
- 需要設計 Telegram Mini App 的 React 架構
- 需要將 Hermes 後台管理系統搬到 TG Mini App 行動端
- 需要按「優先序任務清單」逐步指派 Agent 開發
- 需要確保元件 Props 與型別定義在開發過程中不被偏離

## Prerequisites

- Node.js 18+ 與 npm/yarn/pnpm
- React 18+ + TypeScript 專案基底
- `@telegram-apps/sdk-react` 套件（**不建議使用** — 實測導致白畫面，見下方 Native API 章節。**必須使用原生 `window.Telegram.WebApp` API**）
- `@types/node`（devDependency，用於 `@/` path alias）
- TelegramUI kit（建議 MVP 用 Cell/Card/List 加速開發）
- ECharts（趨勢圖用）
- 一個已註冊的 Telegram Bot 與 Mini App URL（TG 後台設定）
- **Vite 版本注意**：Node.js 18 只能使用 `create-vite@5.x`（`npx create-vite@5`），最新 create-vite 需要 Node 20+

## Quick Reference

| 領域 | 關鍵檔案 | 用途 |
|---|---|---|
| 應用入口 | `src/app/App.tsx` | Provider 包裹 + Router |
| TG 初始化 | `src/app/providers/TelegramProvider.tsx` | SDK init / launch params |
| 路由 | `src/app/router/AppRouter.tsx` | HashRouter + 頁面路由 |
| 夢想儀表板 | `src/pages/dream/DreamDashboardPage.tsx` | 全頁式總覽：KPI 卡片、圓環規、模型延遲條、快速操作、底欄導航 |
| Dashboard | `src/pages/dashboard/DashboardPage.tsx` | 首頁主畫面（舊版） |
| TG 掛鉤 | `src/hooks/telegram/useTelegram*.ts` | 原生按鈕/彈窗/主題綁定 |
| API 層 | `src/services/api/*.api.ts` | 後端資料擷取 |
| 資料轉換 | `src/services/adapters/*.adapter.ts` | API raw data → UI model |
| 圖表 | `src/components/charts/EChartsPanel.tsx` | ECharts 封裝容器 |
| 共用工具 | `src/utils/formatters.ts`, `dates.ts`, `metrics.ts`, `guards.ts` | 格式化/日期/指標/型別守衛 |
| 樣式 | `src/styles/globals.css`, `telegram-theme.css`, `tokens.css` | 全域樣式/TG 主題/CSS token |
| 型別定義 | `references/types-definitions.md` | 9 個 type module 完整定義 |
| 元件 Props | `references/component-props.md` | 5 個核心元件 Props 契約 |
| 控制面板整合 | `references/control-interface-setup.md` | 第三方 hermes-control-interface 安裝與代理配置 |

## File Tree（完整）

```
src/
├─ app/
│  ├─ App.tsx
│  ├─ providers/
│  │  ├─ TelegramProvider.tsx
│  │  └─ ThemeProvider.tsx
│  └─ router/
│     ├─ AppRouter.tsx
│     └─ routes.ts
│
├─ pages/
│  ├─ dashboard/
│  │  ├─ DashboardPage.tsx
│  │  └─ DashboardPage.styles.ts
│  ├─ dream/\n│  │  └─ DreamDashboardPage.tsx\n│  ├─ alerts/AlertsPage.tsx\n│  ├─ chat/ChatPage.tsx\n│  ├─ documents/DocumentsPage.tsx\n│  ├─ analysis/AnalysisPage.tsx\n│  ├─ profile/ProfilePage.tsx\n│  ├─ prompts/PromptFactoryPage.tsx\n│  ├─ logs/LogsPage.tsx\n│  ├─ events/EventsPage.tsx
│  ├─ keys/
│  │  └─ ApiKeysPage.tsx
│  ├─ proxy/ProxyPage.tsx
│  └─ settings/SettingsPage.tsx
│
├─ components/
│  ├─ layout/
│  │  ├─ TelegramAppShell.tsx
│  │  ├─ PageContainer.tsx
│  │  ├─ PageHeader.tsx
│  │  └─ BottomSafeArea.tsx
│  ├─ dashboard/
│  │  ├─ DashboardHeader.tsx
│  │  ├─ EnvironmentChip.tsx
│  │  ├─ StatusOverviewGrid.tsx
│  │  ├─ StatCard.tsx
│  │  ├─ DashboardTabs.tsx
│  │  ├─ TrendPanel.tsx
│  │  ├─ AlertsList.tsx
│  │  ├─ AlertCard.tsx
│  │  ├─ EventsTimeline.tsx
│  │  └─ EmptyStateCard.tsx
│  ├─ charts/
│  │  ├─ EChartsPanel.tsx
│  │  ├─ RequestTrendChart.tsx
│  │  ├─ LatencyTrendChart.tsx
│  │  ├─ ErrorRateChart.tsx
│  │  └─ QuotaTrendChart.tsx
│  ├─ tg/
│  │  ├─ TgBackButtonController.tsx
│  │  ├─ TgMainButtonController.tsx
│  │  ├─ TgSettingsButtonController.tsx
│  │  ├─ TgPopupBridge.tsx
│  │  └─ TgThemeSync.tsx
│  └─ common/
│     ├─ StatusBadge.tsx
│     ├─ MetricDelta.tsx
│     ├─ LoadingBlock.tsx
│     ├─ ErrorBlock.tsx
│     └─ SectionTitle.tsx
│
├─ hooks/
│  ├─ telegram/
│  │  ├─ useTelegramInit.ts
│  │  ├─ useTelegramBackButton.ts
│  │  ├─ useTelegramMainButton.ts
│  │  ├─ useTelegramSettingsButton.ts
│  │  ├─ useTelegramPopup.ts
│  │  ├─ useTelegramTheme.ts
│  │  └─ useTelegramViewport.ts
│  ├─ dashboard/
│  │  ├─ useDashboardData.ts
│  │  ├─ useDashboardFilters.ts
│  │  ├─ useAlertsSummary.ts
│  │  └─ useTrendRange.ts
│  └─ shared/
│     ├─ useAsyncState.ts
│     └─ usePolling.ts
│
├─ services/
│  ├─ api/
│  │  ├─ client.ts
│  │  ├─ dashboard.api.ts
│  │  ├─ alerts.api.ts
│  │  ├─ proxy.api.ts
│  │  └─ settings.api.ts
│  └─ adapters/
│     ├─ dashboard.adapter.ts
│     ├─ alert.adapter.ts
│     └─ chart.adapter.ts
│
├─ types/
│  ├─ common.ts
│  ├─ telegram.ts
│  ├─ dashboard.ts
│  ├─ alert.ts
│  ├─ event.ts
│  ├─ keys.ts
│  ├─ metric.ts
│  ├─ proxy.ts
│  ├─ vm.ts
│  └─ api.ts
│
├─ utils/
│  ├─ formatters.ts
│  ├─ dates.ts
│  ├─ metrics.ts
│  └─ guards.ts
│
├─ styles/
│  ├─ globals.css
│  ├─ telegram-theme.css
│  └─ tokens.css
│
├─ main.tsx
└─ vite-env.d.ts
```

## Procedure

### 1. 建立專案與初始化

```bash
# Node.js 18 使用者：使用 create-vite@5 而非最新版
npm create vite@5 hermes-proxy-console -- --template react-ts
cd hermes-proxy-console
npm install echarts
npm install -D @types/node
```

### 2. 設定 `@/` Path Alias

編輯 `vite.config.ts`：
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

編輯 `tsconfig.app.json`，在 `compilerOptions` 中加入：
```json
"baseUrl": ".",
"paths": { "@/*": ["src/*"] }
```

### 3. 建立完整檔案樹

依上方 **File Tree** 建立所有目錄與 stub 檔案。`types/` 內的型別定義與 `components/` 內的元件 Props 必須完全遵守 `references/types-definitions.md` 與 `references/component-props.md` 中所列的介面。

**核心檔案優先級：**

| 優先 | 檔案 | 原因 |
|---|---|---|
| P0 | `DashboardPage.tsx` + `StatusOverviewGrid.tsx` + `StatCard.tsx` | MVP 核心：首屏摘要 |
| P0 | `TgBackButtonController.tsx` / `TgMainButtonController.tsx` | 導航與關鍵操作 |
| P0 | `api/client.ts` + `api/dashboard.api.ts` | 資料來源 |
| P1 | `TrendPanel.tsx` + charts | 趨勢圖區 |
| P1 | `AlertsList.tsx` / `EventsTimeline.tsx` | 告警與事件 |
| P2 | `ProxyPage.tsx` / `SettingsPage.tsx` | 次要頁面 |

### 4. 實作 Telegram 初始化層

`@telegram-apps/sdk-react` v3 的 API 與 v2 不同 — 元件是物件，包含了 `.mount()` / `.show()` / `.hide()` 等方法；signal 屬性需呼叫取值（`.isVisible()`），用 `.sub(cb)` 訂閱變更。

`src/app/providers/TelegramProvider.tsx`：
```tsx
import { useEffect } from 'react';
import { init, backButton, mainButton, themeParams, viewport } from '@telegram-apps/sdk-react';

export function TelegramProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    try {
      init();
      // 掛載各元件（僅在 Mini App 環境內有效）
      if (backButton.isSupported()) backButton.mount();
      mainButton.mount();
      themeParams.mount();
      viewport.mount();
      // 綁定 CSS 變數
      if (themeParams.isMounted() && !themeParams.isCssVarsBound) themeParams.bindCssVars();
      if (viewport.isMounted() && !viewport.isCssVarsBound) { viewport.bindCssVars(); viewport.expand(); }
    } catch { console.warn('TG SDK init skipped (not in TG Mini App)'); }
    return () => { /* cleanup unmount calls */ };
  }, []);
  return <>{children}</>;
}
```

詳細 API 對照表請參閱 `references/sdk-v3-api.md`。

### 5. 元件對應實作（TelegramUI kit）

每個 UI 區塊對應到 TelegramUI kit 元件。關鍵對應：

```tsx
// 狀態摘要 — Section + Cell
import { Section, Cell } from '@telegram-apps/telegram-ui';

export function StatusOverviewGrid() {
  return (
    <Section header="系統狀態">
      <Cell before={<StatusBadge status="healthy" />}
            subhead="VM · proxy-01"
            after="CPU 23% · Mem 45%">VM 狀態</Cell>
      <Cell before={<StatusBadge status="healthy" />}
            subhead="v2.4.1 · 執行中 12h"
            after={`${activeAgents} 個 Agent`}>Proxy 狀態</Cell>
    </Section>
  );
}
```

| 區塊 | 建議元件 |
|---|---|
| App 外框 | AppRoot + Section + Cell |
| KPI 摘要 | Card/Cell + 自訂 StatCard |
| 分頁切換 | Tabs/Segmented Control |
| 告警列表 | List + Cell + Badge |
| 事件列表 | Section + Cell |
| 趨勢圖區 | 自訂容器 + EChartsPanel |

### 6. 實作 TG 原生操作整合

BackButton / MainButton / SettingsButton / Popup 一律透過 hooks 控制，每個掛鉤只在需要的頁面 mount/unmount。

**⚠️ 注意：v3 SDK 的 mainButton API 與 v2 完全不同。** 沒有 `mainButton.setText()` 或 `mainButton.on('click')` — 改用 `.setParams()` 和 `.onClick()`：

```tsx
import { useEffect } from 'react';
import { mainButton } from '@telegram-apps/sdk-react';

function useMyMainButton(text: string, visible: boolean, onClick: () => void) {
  useEffect(() => {
    mainButton.setParams({ text, isVisible: visible, isEnabled: true });
    mainButton.onClick(onClick);
    return () => {
      mainButton.setParams({ isVisible: false });
      mainButton.offClick(onClick);
    };
  }, [text, visible, onClick]);
}
```

**Popup 使用 `popup.open()` 回傳 Promise：**

```tsx
import { popup } from '@telegram-apps/sdk-react';

const handleRestart = async () => {
  const result = await popup.open({
    title: '確認重啟',
    message: '將中斷 Proxy 服務約 30 秒，確定繼續？',
    buttons: [
      { id: 'cancel', type: 'cancel', text: '取消' },
      { id: 'confirm', type: 'destructive', text: '重啟' },
    ],
  });
  // ⚠️ popup.open() resolves to the button id as a plain string, not { id: string }
  if (result === 'confirm') {
    await proxyApi.action('restart');
  }
};
```

### 7. API 層與資料轉換

`src/services/api/client.ts` — axios/fetch 封裝基底 URL、攔截器、錯誤處理。

```typescript
// dashboard.api.ts — Adapter pattern
import { client } from './client';
export const dashboardApi = {
  getSummary: () =>
    client.get<DashboardRawData>('/dashboard/summary').then(dashboardAdapter),
  getTrend: (range: '24h' | '7d') =>
    client.get<MetricRawData[]>('/dashboard/trend', { params: { range } }).then(chartAdapter),
};
```

`src/services/adapters/` — 後端 raw data → UI model，與型別定義完全對應。

### 8. 建置執行順序（逐步指派 Agent）

每個任務完成後，Agent 需回報：生成了哪些檔案、是否與型別介面一致、是否有偏離檔案樹之處。

```
Phase 1: TelegramAppShell + useTelegramInit → 平台能力可用
Phase 2: DashboardPage 靜態渲染（假資料）→ 驗證版面與元件清單
Phase 3: services/api/dashboard.api.ts 串接真實資料 → 驗證型別契約
Phase 4: AlertsTab / EventsTab 互動邏輯 → 驗證使用者操作路徑
Phase 5: PrimaryActionController（MainButton）→ 驗證高風險操作確認流程
```

## Constraints（不可違反）

- 技術棧固定：React + TypeScript + TelegramUI kit + `@telegram-apps/sdk-react`
- Telegram 原生能力一律透過原生 `window.Telegram.WebApp` API 控制（封裝於 `src/hooks/telegram/index.ts`）。不推薦使用 `@telegram-apps/sdk-react`，實測該套件在某些 TG 客戶端會導致全白畫面崩潰。
- `types/` 只放純型別，`components/` 只放呈現邏輯
- 禁止憑空新增檔案樹以外的目錄結構，如需新增須先提出並更新規格
- MVP 範圍不含：路由規則編輯器、系統設定深度頁面
- 行動端優先，桌面版四段式佈局僅作為未來擴充參考
- **UI 按鈕必須連到真實頁面**：禁止放置「即將上線」或「敬請期待」的 Popup 按鈕。每個按鈕/導航項目必須導向一個有實際內容的頁面。如果某功能尚未實作，該按鈕應隱藏而非顯示後告知無法使用。

## Task 交付格式（供逐步指派 Agent）

```
### Task: [任務名稱]
Context: [這個功能在整個系統的角色]
Spec Reference: [對應本文件第幾節]
Input: [已有的檔案/型別/元件清單]
Expected Output: [具體要生成的檔案清單]
Constraints: [不能做的事、必須遵守的檔案結構]
Verification: [如何驗證這次產出是對的]
```

## Native API 替代方案（當 TG SDK 造成白畫面時）

**`@telegram-apps/sdk-react` v3 在某些 Telegram 客戶端（尤其是舊版 iOS/Android WebView）會導致全白畫面崩潰。** 實測 v3.3.9 在特定環境下 `init()` 或 signal hook 會拋出無法捕捉的例外，使整個 React app 無法渲染。

**解法：使用 `window.Telegram.WebApp` 原生 API**，完全不需要安裝任何套件。

替代 `@telegram-apps/sdk-react` 的方式：

| 功能 | SDK v3 | 原生 API |
|---|---|---|
| BackButton | `backButton.show()`, `.hide()`, `.onClick()` | `window.Telegram.WebApp.BackButton.show()`, `.hide()`, `.onClick()` |
| MainButton | `mainButton.setParams({ text, isVisible })` | `window.Telegram.WebApp.MainButton.setParams({ text, is_visible })` |
| Popup | `popup.open({ title, message, buttons })` → Promise | `window.Telegram.WebApp.showPopup({ title, message, buttons }, cb)` |
| Theme | `themeParams.backgroundColor()` | `window.Telegram.WebApp.themeParams.bg_color` |
| Viewport | `viewport.expand()` | `window.Telegram.WebApp.expand()` |
| 初始化 | `init()` | `window.Telegram.WebApp.ready()` |

原生 API 的優點：
- **不增加 bundle size**（SDK v3 約 60 kB gzip）
- **不依賴第三方套件**，不會因版本升級出現 breaking changes
- **白畫面風險為零** — 原生 API 在 TG Mini App 中 100% 可用，不存在 `init()` 失敗的問題
- **signal 不需要訂閱** — 直接在 useEffect 中讀取值即可

在 hooks 中封裝原生 API 的模式：

```typescript
function getTG() {
  return (window as any).Telegram?.WebApp ?? null;
}

// 範例：useTelegramMainButton（原生版）
export function useTelegramMainButton(
  config: { text: string; visible: boolean; enabled?: boolean; loading?: boolean },
  onClick?: () => void,
) {
  useEffect(() => {
    const tg = getTG();
    if (!tg?.MainButton) return;
    tg.MainButton.setParams({
      text: config.text,
      is_visible: config.visible,
      is_active: config.enabled ?? true,
    });
    if (config.loading) tg.MainButton.showProgress();
    else tg.MainButton.hideProgress();
    if (onClick) tg.MainButton.onClick(onClick);
    return () => {
      tg.MainButton.hide();
      tg.MainButton.hideProgress();
      if (onClick) tg.MainButton.offClick(onClick);
    };
  }, [config.text, config.visible, config.enabled, config.loading, onClick]);
}
```

**Bundle size 影響：** 移除 `@telegram-apps/sdk-react` 後 JS bundle 從 **204 kB → 148 kB**（-27%），gzip 從 **65 kB → 48 kB**。

完整的 hooks 實作位於 `src/hooks/telegram/index.ts`，是使用原生 API 的參考範例。

## Pitfalls

- **SDK v3 API 與 v2 不相容**...
- **型別正確 ≠ 資料正確（最常犯的錯誤）**：tsc 編譯通過不代表資料流正確。
  `DashboardPage.tsx` 用 MOCK_KPIS 常數渲染時，tsc 會通過，但後端 `/api/dashboard` 的資料根本沒被使用。
  修正後的流程：`useDashboardData()` 呼叫 `dashboardApi.status()` → adapter 轉換 → 頁面渲染。
  驗證方式：`curl -s http://localhost:8081/api/dashboard | python3 -m json.tool` 確認 schema 一致。
- **每次修改資料流必須 curl 真實端點**：改 `dashboard.adapter.ts` 或 `dashboard.api.ts` 後，
  不只要 tsc 跑過，還要 `curl localhost:8081/api/dashboard | jq '.overview.kpis | length'` 確認 KPI 數量正確。
- **子代理說 done 不代表接好了**：子代理完成後，必須獨立用 curl 驗證 API 端點回應格式。
  之前 `dashboard.api.ts` 回傳 mock 資料編譯會過但功能是壞的，就是沒做這步。
- **themeParams Signal 永不為 undefined**：v3 SDK 的 `themeParams.backgroundColor` / `textColor` / `hintColor` 等 signal 函式在型別系統中被視為**總是存在**，故 `themeParams.backgroundColor ? themeParams.backgroundColor() : undefined` 觸發 TS2774（condition always true）。應使用 optional chaining：`themeParams.backgroundColor?.()`。
- **backButton.isSupported 是函式**：`backButton.isSupported()` 而非 `backButton.isSupported`。mainButton / themeParams / viewport 沒有 `isSupported`，直接用 `try/catch` 包裹 mount 操作。
- **Signal 訂閱用 `.sub(cb)`**：v3 signal 使用 `.sub(cb)`（回傳 unsub function）和 `.unsub(cb)`，不是 `.on('change', cb)` 或 `.subscribe(cb)`。React 中可用 `useSyncExternalStore` 或 sdk-react 提供的 `useSignal()`。
- **BackButton 全域殘留**：React Router 切頁若沒 cleanup BackButton 監聽器，下一頁會異常觸發返回。每個頁面各自 `useTelegramBackButton`，在 `useEffect` 回傳 cleanup。
- **Groq 金鑰測試注意**：由於 Groq 的 API 設計，透過 `/v1/models` 端點進行的金鑰測試僅能確認網路連線和基礎授權，無法保證金鑰具備實際推理權限。在實務上，即使金鑰被標記為無效，該端點也可能回傳 200。建議在 API 金鑰管理頁面使用「測試金鑰」功能（實際呼叫 `/v1/chat/completions`）以獲得更準確的結果。
- **MainButton 疊加**：兩頁同時 `setParams({ isVisible: true })` 會衝突。MVP 做法：只在 DashboardPage 使用 MainButton。
- **Popup 回傳值型別**：`popup.open()` 回傳 Promise，resolved value 型別依版本而異。實測 v3.3.9 下 await 結果可能是**按鈕 id 字串**（如 `'confirm'`）而非 `{ id: string }` 物件。安全做法：`const result = await popup.open(...); if (result === 'confirm' || result?.id === 'confirm')` 雙重判斷兼容不同 SDK 版本。
- **主題色不可控**：TG ThemeParams 顏色隨用戶主題變動。**狀態燈色（綠/黃/紅/灰）使用固定色值**（`#34c759` / `#ffcc02` / `#ff3b30` / `#8e8e93`），不綁 TG CSS 變數。
- **開發環境模擬**：瀏覽器開發時 `backButton.isSupported()` 回傳 `false`，所有 TG 元件會拋出例外。使用 `try/catch` 包裹 mount 操作，或在 launchParams 中 mock TelegramWebApp。
- **ECharts 容器大小**：viewPort 在 true 模式下含 safe area inset。圖表容器需用 `useViewport()` 取得實際可用高度。
- **API 金鑰測試結果可能因平台而異**：不同平台的金鑰測試端點可靠度不同。Groq 的 `/v1/models` 端點僅驗證連線能力，不代表金鑰可用於實際推理。建議在實際使用中進行額外驗證，並參考具體平台的驗證文件。
- **型別與元件分離**：禁止在元件檔內定義 Props 介面後不同步更新 `types/`。所有 Props 須事先在 `component-props.md` 中定義。
- **Cloudflare 邊緣快取導致舊內容殘留**：deploy 新 build 到 `zhiyan.dev/m/` 後，Cloudflare 可能持續提供舊版 HTML 甚至完全不相干的網站內容（如「只言」站），造成白畫面或錯亂。解法：登入 CF 儀表板 → Caching → Purge Everything。如果無法即時清除，可用 trycloudflare 通道作為臨時替代（`scripts/start-tunnel.py`），注意該 URL 重啟即變。
- **TG Mini App 中 API_BASE 不可用 localhost**：`localhost:8081` 在 TG WebView 中指向用戶手機，而非伺服器。所有 fetch 呼叫需使用**相對路徑**（`/api/keys`），因為 JS 與 API 由同一個後端提供服務（port 8081 的 Python miniapp-server）。
- **SVG 圓環規比 ECharts 更適合簡單的單一數值視覺化**：健康度圓環、進度百分比等只需一個 SVG circle 的 `stroke-dasharray` + `stroke-dashoffset`，不需要載入 60kB 的 ECharts。計算公式：`offset = circumference - (percent/100) × circumference`。注意 `transform="rotate(-90 60 60)"` 讓圓環從頂部開始繪製。
- **底欄導航的 safe-area 處理**：固定底欄必須使用 `paddingBottom: 'env(safe-area-inset-bottom, 8px)'` 避免 iPhone X 以上機型的 Home Indicator 遮擋按鈕。
- **TG WebView 不注入 `--tg-theme-*` CSS 變數 → 全白畫面（🔴 高頻陷阱）**：Telegram Mini App 的 WebView 不一定會設定 `--tg-theme-bg-color` 等 CSS 自訂屬性。當所有元件使用 `var(--tg-theme-bg-color, #fff)` 模式時，若變數未設定，fallback 一律是白色 → 整個 App 白底白字不可讀。**徵兆**：用戶在手機 TG 內看到全白背景，但桌面瀏覽器正常（因為後者主題變數存在）。**解法：不使用 Telegram CSS 變數，直接硬編碼深色主題色值**。一次性全域 sed 替換（處理所有 `.tsx` + `globals.css`）：
  ```bash
  cd src && find . -name '*.tsx' -exec sed -i \
    -e 's|var(--tg-theme-bg-color, #[^)]*)|#0f172a|g' \
    -e 's|var(--tg-theme-secondary-bg-color, #[^)]*)|#1e293b|g' \
    -e 's|var(--tg-theme-text-color, #[^)]*)|#e2e8f0|g' \
    -e 's|var(--tg-theme-hint-color, #[^)]*)|#64748b|g' \
    -e 's|var(--tg-theme-button-color, #[^)]*)|#22c55e|g' \
    -e 's|var(--tg-theme-button-text-color, #[^)]*)|#0f172a|g' \
    -e 's|var(--tg-theme-link-color, #[^)]*)|#38bdf8|g' \
    -e 's|var(--tg-theme-divider-color, #[^)]*)|#334155|g' \
    -e 's|var(--tg-theme-section-separator-color, #[^)]*)|#334155|g' \
    {} +
  ```
  最後也需修復 `globals.css` 中 `body`、`a`、`::-webkit-scrollbar-thumb` 的 CSS 變數。替換後用 `grep -r 'var(--tg-theme-' src/` 確認殘留（僅 dashboard 舊頁面可忽略）。深色主題色碼：背景 `#0f172a`、卡片 `#1e293b`、文字 `#e2e8f0`、提示 `#64748b`、按鈕 `#22c55e`、連結 `#38bdf8`、邊框 `#334155`。

### 10. 夢想儀表板（全頁式總覽）  

參考 `references/dream-dashboard-spec.md` 的設計規格。此頁面風格與原有 Dashboard 不同：

- **全頁式佈局**：不使用 PageContainer / Section / Cell，改用自訂 inline styles 實現深色主題卡片
- **SVG 圓環規**：健康度圓環使用 `SVG stroke-dasharray/stroke-dashoffset`，無需 ECharts。實作方式：
  ```tsx
  function HealthGaugeRing({ percent }: { percent: number }) {
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percent / 100) * circumference;
    const color = percent >= 95 ? '#22c55e' : percent >= 80 ? '#f59e0b' : '#ef4444';
    return (
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none"
          stroke="rgba(148, 163, 184, 0.12)" strokeWidth="8" />
        <circle cx="60" cy="60" r={radius} fill="none"
          stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
    );
  }
  ```
- **底欄導航**：5 個分頁按鈕（儀表板/對話/文件/分析/個人），用 `position: fixed; bottom: 0` + `safe-area-inset-bottom`
- **模型延遲條**：水平進度條，寬度依 `latency / MAX_LATENCY` 計算，顏色依延遲區間（<140ms 綠 / <180ms 黃 / >=180ms 紅）

將 Vite build 產出部署到現有 Python 後端和 nginx：

詳見 `references/deployment.md` — 含 nginx SPA 配置、Python 後端 fallback patch、Cloudflare 快取處理。

快速部署指令：

```bash
cd ~/hermes-proxy-console && npm run build
sudo cp -r dist/* /var/www/brand-site/m/
sudo cp -r dist/* /var/www/brand-site/tg-app/   # Python 靜態路徑
sudo systemctl reload nginx
# 重啟 Python 後端（使用 background terminal）：
sudo pkill -f miniapp-server.py
terminal(background=true): python3 /usr/local/bin/miniapp-server.py 8081
```

## Verification

建置後與部署前，依序執行以下驗證：

**A. 型別與編譯（門檻級）**
1. `npx tsc -b --noEmit` — 0 errors
2. `npm run build` — exit 0

**B. 資料流驗證（之前都跳過這步 — 不能再跳）**
3. `curl -s http://localhost:8081/api/dashboard | python3 -m json.tool > /tmp/dash-api.json`
4. 確認回傳的 `overview.kpis` 包含 **8 項 KPI**（vm_status, proxy_status, active_agents, requests_per_minute, avg_latency, error_rate, quota_usage, alerts_count）
5. 確認 `overview.environment` 是 `"prod"` 或 `"staging"`
6. `curl -s http://localhost:8081/api/keys | python3 -m json.tool` — 確認 keys 陣列非空

**C. 前端渲染驗證**
7. 開啟 TG Mini App，逐一核對首屏狀態燈與 KPI 數字正確呈現
8. 分頁切換（趨勢 / 告警 / 事件）流暢無閃爍
9. 重啟 Proxy 彈出 Popup 確認視窗，取消/確認行為正確
10. 主題跟隨 TG 明暗模式切換（狀態燈色除外）
11. 返回按鈕在非首頁時顯示，點擊回到 Dashboard
12. 所有型別定義與實際 API 回傳結構一致

**D. 金鑰管理驗證**
13. 開啟 API 金鑰管理頁面，確認 8 把金鑰正確顯示
14. 測試 Agnes / DeepSeek 金鑰，確認有效

## References

- `skill_view(name='hermes-proxy-console', file_path='references/types-definitions.md')` — 9 個 type module：common, metric, alert, event, proxy, vm, dashboard, telegram, api
- `skill_view(name='hermes-proxy-console', file_path='references/component-props.md')` — 5 個核心元件 Props 契約（StatCard, DashboardTabs, AlertsList, EventsTimeline, TrendPanel）
- `skill_view(name='hermes-proxy-console', file_path='references/sdk-v3-api.md')` — `@telegram-apps/sdk-react` v3 API 完整對照表：每個元件的 methods / signals / subscription 模式
- `skill_view(name='hermes-proxy-console', file_path='references/deployment.md')` — nginx SPA 配置、Python 後端 fallback、Cloudflare 快取處理策略
- `skill_view(name='hermes-proxy-console', file_path='references/dream-dashboard-spec.md')` — 夢想儀表板設計規格：使用者草圖轉規格，含 7 區塊版面、元件規格、色票、資料需求
- `skill_view(name='hermes-proxy-console', file_path='references/control-interface-setup.md')` — 第三方 hermes-control-interface 安裝、nginx 代理、繁體中文化
- `skill_view(name='hermes-proxy-console', file_path='references/page-pattern.md')` — 頁面建立模式：inline styles、TG 原生 hooks、三態表單、fetch API 呼叫慣例、4 種渲染模式（stats grid / alert table / timeline / info card）
- `skill_view(name='hermes-proxy-console', file_path='references/miniapp-server-endpoints.md')` — 完整 API 端點文件（requests DB schema、所有 GET/POST 端點回應格式、端點新增指引）
- `skill_view(name='hermes-proxy-console', file_path='references/data-verification.md')` — 數據真實性驗證：API→DB→前端三層交叉比對，含 SQLite 查詢模式與常見虛假數據信號
- `skill_view(name='hermes-proxy-console', file_path='scripts/start-tunnel.py')` — 啟動 trycloudflare 隧道並回傳暫用 URL 的 Python 腳本
