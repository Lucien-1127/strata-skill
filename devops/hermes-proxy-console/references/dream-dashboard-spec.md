# Dream Dashboard Design Spec

**來源：** 使用者夢想草圖（2026-07-08）
**目標：** Hermes Proxy Console TG Mini App 的「總儀表板」視覺方向
**狀態：** 設計參考，非強制規格

---

## Overview

A premium, dark-theme management console for an AI legal system (`Hermes v6.6 — 智研 AI 法律系統`).
Combines real-time KPI monitoring, model routing, system health, and quick actions in a single-page dashboard with bottom navigation.

---

## Layout Architecture

```
┌──────────────────────────────┐
│ Brand · User Profile (top bar)│
├──────────────────────────────┤
│ KPI Card Grid (2x2)           │
│ [Chats] [Health] [Tokens] [Cost]│
├──────────────────────────────┤
│ System Health Gauge (Ring)    │
│ + 4 Sub-module status chips   │
├──────────────────────────────┤
│ Model Routing (5 rows + bars) │
├──────────────────────────────┤
│ Quick Actions (2×3 grid)      │
├──────────────────────────────┤
│ Recent Conversations (list)   │
├──────────────────────────────┤
│ Bottom Nav (5 tabs)           │
│ Dashboard Chat Docs Analysis Me│
└──────────────────────────────┘
```

---

## Component Spec

### A. Top Bar
- Left: `HERMES v6.6` brand text with icon
- Right: User avatar (round, classical bust style) + name `陛下` + `PRO` tag (purple badge) + `ID: 10086`

### B. KPI Cards (2×2 Grid)

| Card | Value | Trend | Color |
|------|-------|-------|-------|
| 今日對話 | 1,284 | ↑12.5% (green) | Blue accent |
| 系統狀態 | 96.7% | - | Green (ring) |
| Token 使用 | 256.4K | - | Purple |
| 今日成本 | $0.842 | ↓8.3% (orange) | Orange accent |

Each card: large bold value, small label below, trend indicator top-right corner.

### C. System Health Gauge

- Circular gauge at ~96.7% (green ring via SVG stroke-dasharray)
- Next to gauge: "系統狀態 ● 運行中" label + green trend wave line
- Below gauge: 4 status chips in 2×2 grid:
  - API 路由：5/5 正常 🌐
  - 模型服務：12/12 在線 🧊
  - 資料庫：正常 💾
  - 快取服務：正常 ⚡

Each chip: icon + label + green status indicator.

### D. Model Routing Status

- Section header: "模型路由狀態" + "查看全部 >" link
- 5 rows, each: model name + latency value (ms) + horizontal progress bar (green/yellow):
  - Gemini 1.5 Pro — 128ms (green bar ~85%)
  - Claude 4 Opus — 156ms (green bar ~75%)
  - GPT-4.1 — 198ms (yellow bar ~60%)
  - DeepSeek V3 — 142ms (green bar ~80%)
  - Kimi K2.5 — 168ms (green bar ~70%)
- Bottom: "路由設定 >" button

### E. Quick Actions (2×3 Grid)

6 icon buttons with labels:
1. 開始對話 (blue, chat bubble icon)
2. 上傳文件 (green, cloud upload icon)
3. 知識庫 (purple, book icon)
4. 提示詞工廠 (gold, wand icon)
5. 系統日誌 (blue, document icon)
6. 設定中心 (gray, gear icon)

Each: icon + label text, rounded card, consistent sizing.

### F. Recent Conversations

- Section header: "最近對話" + "查看全部 >" link
- 1+ conversation items showing:
  - Title: legal query text
  - Summary: "與 Claude 4 Opus 的對話 · 2 分鐘前"
  - Message count badge: "32 訊息"
  - Right arrow for navigation

### G. Bottom Navigation

5 icon-based tabs at the bottom of the screen:
1. 儀表板 (home icon) — highlighted/active state
2. 對話 (chat icon)
3. 文件 (document icon)
4. 分析 (chart icon)
5. 我的 (profile icon)

---

## Color Palette (Dark Theme)

| Token | Value | Usage |
|-------|-------|-------|
| bg | `#0f172a` | Main background |
| card bg | `#1e293b` | Card surfaces |
| text | `#e2e8f0` | Primary text |
| muted text | `#94a3b8` | Labels, timestamps |
| accent blue | `#3b82f6` | Primary actions, active tab |
| accent green | `#22c55e` | Health OK, positive trends |
| accent orange | `#f59e0b` | Warning, negative trends |
| accent red | `#ef4444` | Errors |
| accent purple | `#a855f7` | PRO badge, special indicators |

---

## Data Requirements (future)

| Metric | Source | Refresh |
|--------|--------|---------|
| Today's chat count | Hermes state.db sessions | Every 5 min |
| System health % | Gateway health probe | Every 1 min |
| Token usage | FreeLLM DB + Hermes insights | Every 1 min |
| Cost | Token usage × model price | Every 1 min |
| Model latencies | Gateway API per-model probe | Every 5 min |
| Recent conversations | Hermes state.db | On page load |
