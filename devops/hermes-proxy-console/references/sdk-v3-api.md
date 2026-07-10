# @telegram-apps/sdk-react v3 API Surface

實測版本：`@telegram-apps/sdk-react@3.3.9`（依賴 `@telegram-apps/sdk@3.x`）

## 匯入方式

```ts
import {
  init,
  backButton, mainButton, popup, themeParams, viewport,
} from '@telegram-apps/sdk-react';
```

`@telegram-apps/sdk-react` 會 `export * from "@telegram-apps/sdk"`，所以所有 API 都直接從 sdk-react 匯入。

## 初始化

```ts
import { init } from '@telegram-apps/sdk-react';

init(); // 只需呼叫一次，通常在 App 層級
```

## backButton

| 屬性/方法 | 型別 | 說明 |
|---|---|---|
| `.mount()` | `() => void` | 掛載元件 |
| `.unmount()` | `() => void` | 卸載 |
| `.isMounted()` | `() => boolean` | 是否已掛載 |
| `.isSupported()` | `() => boolean` | 當前環境是否支援 |
| `.isVisible()` | `() => boolean` | 原生返回鍵是否可見 |
| `.show()` | `() => void` | 顯示返回鍵 |
| `.hide()` | `() => void` | 隱藏返回鍵 |
| `.onClick(fn)` | `(fn) => void` | 註冊點擊監聽 |
| `.offClick(fn)` | `(fn) => void` | 移除監聽 |

## mainButton

**注意：mainButton 沒有 `.show()` / `.hide()` 方法** — 改用 `setParams()`。

| 屬性/方法 | 型別 | 說明 |
|---|---|---|
| `.mount()` | `() => void` | 掛載 |
| `.unmount()` | `() => void` | 卸載 |
| `.isMounted()` | `() => boolean` | 呼叫取得 |
| `.setParams(updates)` | `(Partial<State>) => void` | **主要控制方法** |
| `.onClick(fn)` | `(fn) => void` | 註冊點擊 |
| `.offClick(fn)` | `(fn) => void` | 移除點擊 |

**Signal 屬性**（呼叫取得當前值，`.sub(cb)` 訂閱變更）：

| Signal | 取值 | 型別 |
|---|---|---|
| `.isVisible` | `mainButton.isVisible()` | `boolean` |
| `.isEnabled` | `mainButton.isEnabled()` | `boolean` |
| `.isLoaderVisible` | `mainButton.isLoaderVisible()` | `boolean` |
| `.text` | `mainButton.text()` | `string` |
| `.backgroundColor` | `mainButton.backgroundColor()` | string |
| `.textColor` | `mainButton.textColor()` | string |
| `.hasShineEffect` | `mainButton.hasShineEffect()` | `boolean` |
| `.state` | `mainButton.state()` | `State` object |

**`setParams` 接受的欄位**：

```ts
mainButton.setParams({
  text: '重啟 Proxy',
  isVisible: true,
  isEnabled: true,
  isLoaderVisible: false,
});
```

## popup

| 屬性/方法 | 型別 | 說明 |
|---|---|---|
| `.open(params)` | `(PopupParams) => Promise<{ id: string }>` | 開啟彈窗，回傳按下的按鈕 id |

`PopupParams`:
```ts
{
  title: string;
  message: string;
  buttons: Array<{ id: string; type: 'default' | 'destructive' | 'cancel'; text: string }>;
}
```

## themeParams

| 屬性/方法 | 型別 | 說明 |
|---|---|---|
| `.mount()` | `() => void` | 掛載 |
| `.unmount()` | `() => void` | 卸載 |
| `.isMounted()` | `() => boolean` | 是否已掛載 |
| `.isCssVarsBound` | `() => boolean` | CSS 變數是否已綁定 |
| `.bindCssVars()` | `() => void` | 綁定 CSS 變數到 document |

**Signal 屬性**（呼叫取得當前顏色值）：

| Signal | 說明 |
|---|---|
| `.backgroundColor` | 背景色 |
| `.textColor` | 文字色 |
| `.hintColor` | 提示色 |
| `.linkColor` | 連結色 |
| `.buttonColor` | 按鈕色 |
| `.buttonTextColor` | 按鈕文字色 |
| `.secondaryBackgroundColor` | 次要背景色 |
| `.isDark` | 是否深色模式（boolean） |

## viewport

| 屬性/方法 | 型別 | 說明 |
|---|---|---|
| `.mount()` | `() => void` | 掛載 |
| `.unmount()` | `() => void` | 卸載 |
| `.expand()` | `() => void` | 展開到全高度 |
| `.bindCssVars()` | `() => void` | 綁定 safe area 變數 |
| `.isCssVarsBound` | `() => boolean` | 已綁定？ |
| `.isMounted()` | `() => boolean` | 已掛載？ |

**Signal 屬性**（呼叫取得數值）：
`.width`, `.height`, `.stableHeight`, `.isExpanded`, `.isStable`, `.contentSafeAreaInsets`, `.safeAreaInsets` 等。

## Signal 訂閱模式

所有 signal 屬性支援 `.sub(cb)` / `.unsub(cb)` 模式：

```ts
const unsub = themeParams.backgroundColor.sub(() => {
  console.log('背景色變了:', themeParams.backgroundColor());
});
// 清除時呼叫
unsub();
```

React 中建議用 `useSyncExternalStore`：
```ts
const bgColor = useSyncExternalStore(
  (cb) => { const u = themeParams.backgroundColor.sub(cb); return () => u(); },
  () => themeParams.backgroundColor(),
);
```

或直接用 sdk-react 提供的 `useSignal`：
```ts
import { useSignal } from '@telegram-apps/sdk-react';
const bgColor = useSignal(themeParams.backgroundColor);
```
