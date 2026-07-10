# React 空白頁除錯：`new URL()` crash 模式

## 症狀

- 後端 API 回 200 OK，資料完整（curl 驗證正常）
- 登入成功拿得到 token
- 前端頁面全白，無任何 UI 元素顯示
- **手機瀏覽器尤其無聲無息** — 無 console，無 error dialog

## 根因

```tsx
// DashboardPage.tsx (before fix)
{m.worst_entry
  ? new URL(m.worst_entry).hostname   // 💥 "api.cerebras.com" → TypeError!
  : "—"}
```

`new URL()` 要求合法 URL（含 protocol）。後端回傳 bare hostname（如 `api.cerebras.com`、`localhost:8080`）時直接拋 `TypeError`。

React 渲染階段的未捕獲例外 → component tree 完全 unmount → 全白。

## 偵錯步驟

1. **確認後端正常**：
   ```bash
   curl -sk https://lucien126.com/m/api/dashboard -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'][0]['worst_entry'])"
   ```
   若回 bare hostname（無 `https://`）→ 這就是 bug。

2. **檢查前端 build 是否含 fix**：
   ```bash
   BUNDLE=$(ls -t /var/www/brand-site/m/assets/index-*.js | head -1)
   grep -o 'safeHostname' "$BUNDLE" | wc -l
   ```
   若 = 0 → 尚未部署 fix。

## 二層修復

### Layer 1：Safe URL wrapper（治本）

```tsx
function safeHostname(raw: string | null | undefined): string {
  if (!raw) return "—";
  try {
    return new URL(raw.startsWith("http") ? raw : "https://" + raw).hostname;
  } catch {
    return raw; // fallback
  }
}
```

所有消費 API 資料的 `new URL()` 調用都必須經此 wrapper。

### Layer 2：React ErrorBoundary（防禦）

```tsx
class ErrorBoundary extends Component<{ children: React.ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(e: Error) { return { error: e }; }
  render() {
    if (this.state.error) {
      return (
        <div className="empty">
          <div className="empty-icon">💥</div>
          畫面異常：{this.state.error.message}
          <button onClick={() => window.location.reload()}>重新整理</button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

包在 App component 最外層。任何渲染階段 crash 都會被 catch，顯示錯誤訊息而非全白。

## 預防規則

> **所有來自 API 的字串若會餵進 `new URL()`，一律經 `safeHostname()` / try-catch wrapper。**

這包含：`worst_entry`、`base_url`、`endpoint`、任何 user-provided URL 欄位。
