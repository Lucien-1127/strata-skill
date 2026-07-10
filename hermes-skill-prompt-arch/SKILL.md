---
name: hermes-skill-prompt-arch
description: "Hermes 多技能提示詞架構設計"
---
# hermes-skill-prompt-arch

## 📖 Description

Hermes 多技能提示詞架構設計

---

# 🤖 Hermes 多技能提示詞架構

## 功用
Hermes 多技能系統的提示詞架構設計指南，含系統提示詞與技能的互動方式、優先級規則、路由設計，以及 SOUL.md 自動路由實作模式。

## 核心設計
- **SOUL.md** 作為基底系統提示詞（Slot #1）— 內嵌完整技能路由表
- **SKILL.md** 技能提示詞（Slot #2+）— 各技能的領域知識
- 技能路由（關鍵字/意圖匹配）— 自動對照 SOUL.md 路由表載入
- 衝突解決策略

---

## 🔄 SOUL.md 自動路由模式（推薦實作）

### 原理
將路由表嵌入 SOUL.md（每次 session 自動注入 system prompt 的 Slot #1），agent 收到任務時自行對照關鍵字載入對應 skill，無需使用者手動指定。

### 路由表格式
以 Markdown 表格分類組織，每個技能綁定觸發詞：

```markdown
### 📝 摘要/處理
| 觸發詞 | 自動載入 |
|--------|---------|
| 摘要、總結、提煉、重點 | `core-summarizer` |
| 校對、糾錯、語法檢查 | `proofreader` |
```

### 分類結構
| 分類 | 範圍 |
|------|------|
| 📝 摘要/處理 | 摘要、校對、翻譯、簡化、剪輯 |
| ✍️ 寫作 | 文案、社群貼文、筆記 |
| 🖼️ 圖像/影片 | 生圖、影片提示詞、動畫 |
| 🧠 Prompt 工程 | 審查、生成、DSL、策略 |
| 🏗️ Obsidian 工具 | 排版、命名、架構、維護 |
| ⚙️ DevOps / 系統 | GCP、Windows、Kanban、路由 |
| 🔬 研究 / MLOps | 深度研究、記憶、審計 |
| 🌐 其他 | QA、社群工具 |

### 路由規則
1. 收到任務時先對照路由表，自動載入對應 skill
2. 不需要使用者說「載入 XX 技能」
3. 多匹配時：精準匹配 > 類別匹配 > 通用能力
4. 無匹配時用通用能力處理
5. 技能執行完後才產出最終回應

### 實作步驟
1. `skills_list()` 取得所有技能與描述
2. 按類別分組，定義每個技能的觸發關鍵詞
3. 寫入 `~/.hermes/SOUL.md`
4. 新 session 自動生效（SOUL.md 是 slot #1 system prompt）

### Windows 路徑地雷
`write_file` 不接受 MSYS 風格的 `/c/Users/...` 路徑——它會錯誤解析為 `C:\c\Users\...`。**必須用 `C:/Users/...` （正斜線）或純 Windows 路徑。**

---

## 📎 參考檔案
- `references/soul-routing-table-template.md` — 完整路由表格式範本（80 技能）

## 來源
原檔: 知識庫/🔧代理管理/🤖 Hermes多技能提示詞架構.md
