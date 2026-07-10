# React Auth Expiry Pattern — `auth-expired` 事件驅動

## 問題

SPA 使用 module-level `let token = localStorage.getItem("token")` 快取 token。當 API 回 401 時，
`clearToken()` 清除了 localStorage 但 **React state (`loggedIn`) 沒有更新**，導致：

1. Dashboard 頁面持續渲染
2. Dashboard 的 `useEffect([])` 只在 mount 時呼叫 `getDashboard()`
3. `getDashboard()` → 401 → `apiFetch` 清除 token → throw error
4. Error UI 顯示「重試」按鈕
5. 使用者按重試 → `load()` → 又 401 → 又 error
6. **無限迴圈** — 登入頁永遠不會出現，0 次 login POST

## 觸發條件

- 使用者有舊 token 殘留 localStorage（例如從舊版 app 遺留，或 token 過期）
- App 初始化 `loggedIn = !!getToken()` → `true`（舊 token truthy）
- 所有受保護 API 回 401，但 `loggedIn` 狀態不變

## 🔴 重要前置條件：FastAPI 的 `detail` 包裝

FastAPI 的 `HTTPException(detail=...)` 會將錯誤包裝為 `{"detail": ...}` 格式，**而非** `{"error": ...}`。

```json
// 後端實際回傳（FastAPI HTTPException）
{"detail": {"error": {"code": "UNAUTHORIZED", "message": "Token 無效"}}}

// ❌ 前端如果用 json.error?.code 檢查 → 永遠 undefined → 401 處理永不觸發
```

**修復：** 前端必須同時檢查兩種格式：

```ts
const errCode = json.detail?.error?.code || json.error?.code;
const errMsg = json.detail?.error?.message || json.error?.message;
```

如果只檢查 `json.error.code`，401 回傳會被當作普通的「請求失敗」throw 出去，`clearToken()` / `auth-expired` **完全不會執行**，導致 auth loop。

驗證：`curl https://lucien126.com/m/api/dashboard -H "Authorization: Bearer bad"` → 確認回傳的是 `{"detail": {"error": ...}}` 還是 `{"error": ...}`。

---

## 修復：`window.dispatchEvent(new Event("auth-expired"))`

```ts
// api.ts — 在 apiFetch 的 401 處理中（含 FastAPI detail 相容）
const json = await res.json();
const errCode = json.detail?.error?.code || json.error?.code;
const errMsg = json.detail?.error?.message || json.error?.message;

if (errCode === "UNAUTHORIZED") {
  clearToken();
  window.dispatchEvent(new Event("auth-expired"));  // ← 通知 App
  throw new Error(errMsg || "請重新登入");
}
if (errCode) {
  throw new Error(errMsg || "請求失敗");
}
```

```tsx
// App.tsx — 監聽 auth-expired 事件
import { useState, useEffect } from "react";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getToken());

  useEffect(() => {
    const handler = () => setLoggedIn(false);  // ← 強制切回登入頁
    window.addEventListener("auth-expired", handler);
    return () => window.removeEventListener("auth-expired", handler);
  }, []);

  if (!loggedIn) {
    return <LoginPage onLogin={() => setLoggedIn(true)} />;
  }
  // ... app content
}
```

## 優點

- 不需要 React Context / Redux，零依賴
- 任何元件、任何 API 呼叫都可以觸發
- App 層單一監聽點，自動重新渲染

## 偵錯方法

從 nginx access log 確認：

```bash
sudo grep "42.79.35.124" /var/log/nginx/access.log | tail -15
```

若看到：
- `GET /m/api/dashboard` → **401**（重複多次）
- **完全沒有** `POST /m/api/auth/login`

→ 100% 是 auth loop bug，登入頁沒出現。

## 相關檔案

- `/home/ysga1/hermes-miniapp/frontend/src/api.ts` — `apiFetch` 401 處理
- `/home/ysga1/hermes-miniapp/frontend/src/App.tsx` — `auth-expired` 監聽
