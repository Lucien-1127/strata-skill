# Hermes Proxy Console — Page Creation Pattern

## When to Use

Creating a new full-page view (not a component) for the TG Mini App. All pages share the same structural DNA — header bar, back navigation, scrollable content, inline CSS variables, native `window.Telegram.WebApp` hooks.

## Anatomy of a Page

Every page is structured as three layers:

```
<div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
  ├── <header>      ← fixed bar: ← back button + title
  ├── <PageContainer>  ← scrollable content zone (padding: '16px 16px 100px')
  │   ├── loading / empty / error states
  │   ├── main content (cards, lists, forms)
  │   └── action buttons
  └── </PageContainer>
</div>
```

## Canonical Imports

```typescript
import { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '../../components/layout/PageContainer';
import { useTelegramPopup, useTelegramBackButton } from '../../hooks/telegram/index';
import type { KeyItem } from '../../types/keys';
```

- `PageContainer` — wraps content with safe bottom padding for TG Mini App (100px).
- `useTelegramPopup` — provides `openPopup(title, message, buttons)` returning `Promise<{id: string} | null>`.
- `useTelegramBackButton(visible, handler)` — shows/hides TG BackButton; cleanup on unmount is automatic.
- All type imports from `../../types/`.

## Inline Style Constants Pattern

Define style objects at module level (outside the component) to avoid re-allocation on every render:

```typescript
const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  padding: '12px 16px',
  borderBottom: '1px solid var(--tg-theme-hint-color, #ccc)',
  background: 'var(--tg-theme-bg-color, #fff)',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  fontSize: 16,
  border: '1px solid var(--tg-theme-hint-color, #ccc)',
  borderRadius: 10,
  background: 'var(--tg-theme-bg-color, #fff)',
  color: 'var(--tg-theme-text-color, #000)',
  outline: 'none',
  boxSizing: 'border-box',
};

const btnPrimaryStyle: React.CSSProperties = {
  width: '100%',
  padding: '14px',
  fontSize: 16,
  fontWeight: 600,
  border: 'none',
  borderRadius: 10,
  background: 'var(--tg-theme-button-color, #40a7e3)',
  color: 'var(--tg-theme-button-text-color, #fff)',
  cursor: 'pointer',
};

const btnOutlineStyle: React.CSSProperties = {
  padding: '8px 16px',
  fontSize: 14,
  fontWeight: 500,
  border: '1px solid var(--tg-theme-button-color, #40a7e3)',
  borderRadius: 8,
  background: 'transparent',
  color: 'var(--tg-theme-button-color, #40a7e3)',
  cursor: 'pointer',
};

const btnDangerStyle: React.CSSProperties = {
  width: '100%',
  padding: '14px',
  fontSize: 16,
  fontWeight: 600,
  border: 'none',
  borderRadius: 10,
  background: '#ff3b30',
  color: '#fff',
  cursor: 'pointer',
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: 'var(--tg-theme-hint-color, #999)',
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};
```

### CSS Variable Reference

| Variable | Fallback | Use |
|---|---|---|
| `--tg-theme-bg-color` | `#fff` | Page / card backgrounds |
| `--tg-theme-secondary-bg-color` | `#efeff4` | Card tint, disabled inputs |
| `--tg-theme-text-color` | `#000` | Primary text |
| `--tg-theme-hint-color` | `#999` | Secondary text, borders, section labels |
| `--tg-theme-button-color` | `#40a7e3` | Primary buttons, links, accent |
| `--tg-theme-button-text-color` | `#fff` | Text on primary buttons |

**Exception**: Status dots (green/yellow/red/grey) use fixed hex colors (`#34c759`, `#ffcc02`, `#ff3b30`, `#8e8e93`) — never theme variables, because they must remain identifiable regardless of user theme.

## Three-View State Machine Pattern

A common pattern for data management pages (keys, configs, etc.) is a three-state form mode:

```typescript
type FormMode = 'none' | 'add' | 'edit';

const [showForm, setShowForm] = useState<FormMode>('none');
const [editTarget, setEditTarget] = useState<SomeType | null>(null);
```

**Render branching**:
```typescript
if (showForm === 'add')  return <AddFormView />;
if (showForm === 'edit' && editTarget) return <EditFormView />;
return <ListView />;
```

**Back button routing** — single `handleBack` covers both form-cancel and page-back:
```typescript
useTelegramBackButton(showForm !== 'none', handleBack);

function handleBack() {
  if (showForm !== 'none') {
    setShowForm('none');
    setEditTarget(null);
    resetForm();
  } else {
    onBack();
  }
}
```

## API Call Pattern

All calls use `apiFetch()` which automatically attaches the JWT Bearer token. ⚠️ **NEVER use `http://localhost:8081` as API_BASE** — in TG Mini App, `localhost` refers to the user's mobile device, not the server. Use relative paths instead.

```typescript
import { apiFetch } from '../../hooks/useApi';

const API_BASE = '';
```

```typescript
// GET — fetch list with auth
const fetchKeys = useCallback(async () => {
  try {
    setLoading(true);
    const res = await apiFetch(`${API_BASE}/api/keys`);
    const data = await res.json();
    if (data.keys) setKeys(data.keys);
  } catch {
    // silently fail — user sees empty/error state
  } finally {
    setLoading(false);
  }
}, []);

useEffect(() => { fetchKeys(); }, [fetchKeys]);

// POST — create / update / delete
async function handleAction() {
  setSubmitting(true);
  try {
    const res = await apiFetch(`${API_BASE}/api/keys/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.success) {
      await openPopup('✅ 成功', '操作完成', [
        { id: 'ok', type: 'default', text: '確定' },
      ]);
      await fetchKeys();  // refresh
    }
  } catch {
    await openPopup('❌ 失敗', '無法連線至伺服器', [
      { id: 'ok', type: 'default', text: '確定' },
    ]);
  } finally {
    setSubmitting(false);
  }
}
```

`apiFetch` automatically:
- Reads JWT token from `localStorage('token')`
- Adds `Authorization: Bearer <token>` header
- On 401 response → clears token → redirects to `/m/login.html`
- Does NOT add auth header for `/api/auth/login` itself

See `references/jwt-auth.md` for full implementation (backend + frontend).
```

### Button Disabled Pattern

Disable + reduce opacity during submission to prevent double-taps:

```typescript
<button
  onClick={handleSubmit}
  disabled={submitting || !formLabel.trim()}
  style={{
    ...btnPrimaryStyle,
    opacity: submitting || !formLabel.trim() ? 0.5 : 1,
  }}
>
  {submitting ? '送出中…' : '送出'}
</button>
```

### Confirmation Popup Pattern

Use `openPopup` with both `cancel` and `destructive` buttons:

```typescript
const confirm = await openPopup(
  '⚠️ 刪除確認',
  '此操作無法復原。確定繼續？',
  [
    { id: 'cancel', type: 'default', text: '取消' },
    { id: 'confirm', type: 'destructive', text: '刪除' },
  ],
);
if (!confirm || confirm.id !== 'confirm') return;
```

## Key API Endpoints

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| GET | `/api/keys` | — | `{ keys: KeyItem[], platforms?: string[] }` |
| POST | `/api/keys/add` | `{ platform, label, key }` | `{ success, platform }` |
| POST | `/api/keys/replace` | `{ id, label?, key? }` | `{ success, platform }` |
| POST | `/api/keys/delete` | `{ id }` | `{ success }` |
| POST | `/api/keys/test` | `{ id }` | `{ result: { status, http_code? } }` |

## Type: KeyItem

```typescript
interface KeyItem {
  id: string | number;
  platform: string;
  label: string;
  prefix: string;        // e.g. "sk-abc..."
  added_at: string;       // ISO timestamp
  tested: boolean;        // true after at least one test
  valid: boolean | null;  // true=valid, false=invalid, null=not yet tested
  last_tested?: string;
  test_result?: { status: string; http_code?: number };
  env_file?: string;
}
```

## Existing Page Component Props

All page-level components accept at least `onBack: () => void`. The router passes this as a navigation callback.

```typescript
interface ApiKeysPageProps {
  onBack: () => void;
}
```

## Stats Grid (2×N Big Number Cards)

For dashboard sub-pages that need a rapid-glance stats summary (request counts, errors, rates):

```tsx
<div style={{
  background: 'var(--tg-theme-bg-color, #1a1a2e)',
  borderRadius: 10, padding: 14,
  border: '1px solid var(--tg-theme-hint-color, #333)',
}}>
  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
    <div style={{ textAlign: 'center', padding: '10px 0' }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--tg-theme-text-color, #fff)' }}>
        {value.toLocaleString()}
      </div>
      <div style={{ fontSize: 11, color: 'var(--tg-theme-hint-color, #999)', marginTop: 4 }}>
        {label}
      </div>
    </div>
  </div>
</div>
```

- Dynamic color on the big number for warning thresholds: `color: (value > threshold) ? '#e74c3c' : '#2ecc71'`
- Use `toLocaleString()` for comma-separated formatting.
- Use `grid-template-columns: '1fr 1fr'` for 4 metrics in 2 rows.

## Alert Table View

For data with >1 column that benefits from sortable columns (time, source, status, message):

```tsx
<div style={{ overflowX: 'auto' }}>
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
    <thead>
      <tr style={{ borderBottom: '1px solid var(--tg-theme-hint-color, #333)' }}>
        <th style={{ padding: '8px 6px', textAlign: 'left', color: 'var(--tg-theme-hint-color, #999)' }}>Column</th>
      </tr>
    </thead>
    <tbody>
      {items.map(item => (
        <tr key={item.id} style={{ borderBottom: '1px solid var(--tg-theme-hint-color, #222)' }}>
          <td style={{ padding: '10px 6px', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.value}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

- Keep tables narrow — TG Mini App screens are phone-width. Use `maxWidth` + `textOverflow: 'ellipsis'` for overflow-prone columns.
- Timestamps: `created_at.replace('T', ' ').substring(0, 19)` strips ISO T for mobile.

## Timeline Event Feed

For a chronologically-sorted mixed-type event stream (successes interleaved with errors):

```tsx
{events.map((ev, idx) => (
  <div key={idx} style={{
    display: 'flex', alignItems: 'flex-start', padding: '10px 0',
    borderBottom: '1px solid var(--tg-theme-hint-color, #1a1a2e)', gap: 10,
  }}>
    <div style={{
      width: 10, height: 10, borderRadius: '50%', marginTop: 5, flexShrink: 0,
      background: ev.type === 'error' ? '#e74c3c' : '#2ecc71',
    }} />
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 12, color: 'var(--tg-theme-hint-color, #999)', marginBottom: 2 }}>
        {ev.timestamp}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--tg-theme-text-color, #fff)', marginBottom: 2 }}>
        {ev.title}
      </div>
      <div style={{
        fontSize: 11, display: 'inline-block', padding: '2px 8px', borderRadius: 10,
        background: ev.type === 'error' ? 'rgba(231,76,60,0.15)' : 'rgba(46,204,113,0.15)',
        color: ev.type === 'error' ? '#e74c3c' : '#2ecc71',
      }}>
        {ev.type === 'error' ? '❌ 錯誤' : '✅ 成功'}
      </div>
    </div>
  </div>
))}
```

- Perfect for merging two sorted lists (recent + errors → sort by timestamp → interleave).
- Dot + content layout as vertical timeline. Dot color is the status indicator.
- `flex: 1, minWidth: 0` prevents content overflow in nested flex layouts.

## Info Card Section (Settings Profile)

For read-only profile/info pages with key-value grouped into cards:

```tsx
<div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
  {cards.map(card => (
    <div key={card.label} style={{
      background: 'var(--tg-theme-bg-color, #1a1a2e)',
      borderRadius: 10, padding: 14,
      border: '1px solid var(--tg-theme-hint-color, #333)',
    }}>
      <div style={{ fontSize: 11, color: 'var(--tg-theme-hint-color, #999)', marginBottom: 4 }}>
        {card.label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--tg-theme-text-color, #fff)' }}>
        {card.value}
      </div>
      {card.children}
    </div>
  ))}
</div>
```

- Each card: label (small muted), value (large bold), optional children (tags, sub-metrics).
- Tag lists: `flexWrap: 'wrap', gap: 4` with `background: 'rgba(64,167,227,0.15)', padding: '2px 8px', borderRadius: 8`.

## Pitfalls

- **`as const` tuples and `useState` type narrowing**: If a platform list is declared `as const`, the first element's literal type becomes the state type (e.g. `"groq"` instead of `string`). Declare platform lists as `string[]` when used with uncontrolled select inputs.
- **`fetchKeys` stability**: Wrap in `useCallback` with empty deps (`[]`). It captures no state directly so it never becomes stale. This avoids infinite re-fetch loops when passing it to `useEffect`.
- **Multiple form modes share `handleBack`**: The BackButton hook registers a single callback. Using one handler that checks `showForm` avoids stale-closure bugs from re-registering the hook on every mode change.
- **Submitting state blocks** all buttons in the form view via a single `submitting` boolean — no per-button loading. This is intentional: the backend is single-threaded and double-taps would produce duplicate inserts.
- **Status dots use fixed colors**: As noted in the style section — always hardcode green/red/yellow/grey for status indicators so they are readable regardless of TG theme.
