# React Router 瘦身模式

## 場景

Mini App 經過多次迭代累積了大量空殼頁面（14 頁中只有 5 頁有真實後端），導致：
- 導覽混亂
- 用戶點進空頁面 = 體驗差
- Bundle 膨脹
- TypeScript 型別過度耦合

## 瘦身 5 步驟

### 1. 審計 — 哪些頁面有真實 API？

```
ApiStatusPage  → /api/status  ✅
AlertsPage     → /api/alerts  ✅
ProxyPage      → /api/proxy/status ✅
ApiKeysPage    → /api/keys (CRUD) ✅
SettingsPage   → /api/settings ✅
DreamDashboardPage → 全 mock ❌
ChatPage       → 無後端 ❌
DocumentsPage  → 無後端 ❌
AnalysisPage   → 無後端 ❌
ProfilePage    → 空殼 ❌
PromptFactoryPage → 空殼 ❌
LogsPage       → 空殼 ❌
KnowledgePage  → 空殼 ❌
EventsPage     → 空殼 ❌
```

### 2. 簡化 routes.ts — 只保留有效路由

```typescript
// 瘦身前（15 個路由）
export type AppRoute = '/dashboard' | '/alerts' | '/events' | '/proxy' | '/settings' | '/keys' | '/api-status' | '/dream' | '/chat' | '/documents' | '/analysis' | '/profile' | '/prompts' | '/logs' | '/knowledge';

// 瘦身後（5 個路由）
export type AppRoute = '/api-status' | '/alerts' | '/proxy' | '/keys' | '/settings';
```

### 3. 清理 AppRouter — 移除未使用的 lazy import

```typescript
// 瘦身前：14 個 lazy() import
// 瘦身後：5 個 lazy() import

const ApiStatusPage = lazy(() => import('../../pages/api-status/ApiStatusPage'));
const AlertsPage = lazy(() => import('../../pages/alerts/AlertsPage'));
const ProxyPage = lazy(() => import('../../pages/proxy/ProxyPage'));
const ApiKeysPage = lazy(() => import('../../pages/keys/ApiKeysPage'));
const SettingsPage = lazy(() => import('../../pages/settings/SettingsPage'));
```

### 4. TypeScript 會幫你抓到殘留引用

移除 DashboardPage 後，`handleRestartProxy` 變成 unused declaration：
```
error TS6133: 'handleRestartProxy' is declared but its value is never read.
```

**不要忽略 — 這是信號：還有 hook/state/function 只被已刪除的頁面引用。**

### 5. 驗證打包體積

瘦身前：18 files（含 9 個無用頁面的 chunk）
瘦身後：9 files（5 頁面 + 共用元件）
49 modules（vs 原 68+ modules）

---

## 底部導覽列加入後的 PageContainer 衝突

`PageContainer` 原有 `padding: '16px 16px 100px'` — 100px 底部是給**沒有導覽列**時用的。

加入底部導覽列後，頁面內容底部被導覽列遮住 → 100px 多餘。

**解法：** 將 padding 改為 `padding: '16px 16px 80px'`（80px = nav bar 高度 + safe area）。

## nginx reload 陷阱

```bash
# ❌ 當 nginx 不是 systemd 啟動時（例如直接 nginx 命令啟動）
sudo systemctl reload nginx
# → "nginx.service is not active, cannot reload."

# ✅ 直接送 signal
sudo nginx -s reload
```

檢查：`ps aux | grep nginx` — 如果 PID 不是 systemd 管理的，用 `nginx -s reload`。
