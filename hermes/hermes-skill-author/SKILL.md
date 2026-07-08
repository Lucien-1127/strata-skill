---
name: hermes-skill-author
description: Author Hermes SKILL.md files with quality scoring.
version: 0.4.0
author: Hermes
metadata:
  hermes:
    tags: [Hermes, Skill, Authoring, Quality-Gate]
---

# Hermes 技能工廠

生成符合 Hermes 官方標準的 SKILL.md 技能檔，使用 HARDLINE_RULES 量化評分，支援快速生成、品質閘門自檢與 FEG 極限壓縮。三條鐵則：**description 不可超過 60 字元**、**技能內容可重用而非一次性**、**品質閘門在寫入前執行**。

不包含通用提示詞生成 — 這僅用於 Hermes `skill_manage` 技能製作。

**擴展用法**：如需將外部研究文檔深度整合至既有技能（非從零建立），參見 `references/deep-doc-integration.md`。
**技能架構設計**：每份 SKILL.md 可同時承載 Hook / State Machine / FEG 三種模式，詳見 `references/architecture-patterns.md`。

## When to Use

- "幫我建立一個技能"
- "將這個流程寫成 skill"
- "創建一個 Hermes skill"
- "把這個工作流程存成可重用技能"
- "需要把這個做法 skill 化"

## Prerequisites

- `skill_manage` tool available in the Hermes agent.
- `skill_view` for reading existing skills.
- `skills_list` for checking existing skill names (避免重名).

## 標準：金鑰管理（跨技能共同約定）

所有調用外部 API 的技能**必須**遵循模組化 `.env` 模式，金鑰不可寫入 SKILL.md 或硬編碼在腳本中。

```
~/.hermes/env/
├── agnes.env        # Agnes API key
├── deepseek.env     # DeepSeek API key
├── freellmapi.env   # FreeLLM API key
└── telegram.env     # Telegram bot token
```

腳本讀取金鑰的標準做法（適用於 cron 環境，不依賴 `.bashrc`）：
```python
ENV_PATH = os.path.expanduser("~/.hermes/env/<provider>.env")
key = ""
if os.path.isfile(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            m = re.match(r'^\s*<VAR_NAME>=(.*)$', line.strip())
            if m: key = m.group(1).strip("\"'")
```

Prerequisites 段落應寫「金鑰在 `~/.hermes/env/<provider>.env`」，不可貼真實金鑰。

## How to Run

1. Parse user's task/procedure → extract steps
2. Map to Hermes SKILL.md body sections
3. Apply HARDLINE_RULES → score → quality gates → repair if needed
4. Write via `skill_manage(action="create")`

## Procedure

### R0 — 需求解析

從用戶輸入中提取：

- **來源**：對話歷史、貼上的流程、URL、現有 skill 需改進
- **任務類型**：從頭建立 | 從對話提煉 | 合併/改進現有 skill
- **輸出名稱**：`lowercase-hyphenated`，≤64 字元

資訊不足時，提問補足。

### R1 — 結構選取

從以下三種範本選取最接近的：

| 範本 | 適用情境 | 長度 |
|------|---------|------|
| **標準** | 多步驟操作流程（5+ 工具調用） | ~150-200 行 |
| **輕量** | 單一查詢或 API 調用（< 5 步驟） | ~80-120 行 |
| **參考** | 純知識性參考（無操作步驟） | ~50-80 行 |

### R2 — 骨架生成

生成對應的 YAML frontmatter + 空白段落：

```yaml
---
name: lowercase-hyphenated-name   # ≤64 chars, no spaces
description: One sentence ≤60 chars ends with period.  # ★ 最常違規
version: 0.1.0
author: Hermes                      # 固定值，非環境變數
# platforms: [linux, macos]         # 僅當用到 OS 原生工具
metadata:
  hermes:
    tags: [Capitalized, Relevant, Tags]
---
```

body sections（依序）：

```
# Human Title
2-3 sentence intro: what/does not do/dependency stance

## When to Use
bullet list of concrete trigger phrases

## Prerequisites
exact env vars, install steps, credentials

## How to Run
canonical invocation through Hermes tools

## Quick Reference
flat command/endpoint list, no narration

## Procedure
numbered steps with copy-paste-exact commands

## Pitfalls
known limits, rate limits, things that look broken but aren't

## Verification
single command/check that proves the skill worked
```

### R3 — 內容填充

依序填入以下規則：

**Hermes-tool framing** — 強制使用 Hermes 工具名稱：
- `terminal`（非 cat/grep/ls/sed/awk）
- `read_file`（非 cat/head/tail）
- `search_files`（非 grep/rg/find/ls）
- `patch`（非 sed/awk）
- `write_file`（非 echo/heredoc）
- `execute_code`（非 python3 -c）
- `memory`、`cronjob`、`skill_view`、`skill_manage`

**description ≤60 characters**：
```
Good (57): Author Hermes SKILL.md files with quality scoring.
Bad  (133): A comprehensive skill for authoring Hermes SKILL.md files that includes quality gates and FEG compression.
```

**禁止詞**：`powerful` / `comprehensive` / `seamless` / `advanced` / `robust`

**author=Hermes** — 永遠填 `Hermes`，不從環境變數、git config、OS username 讀取。

### R4 — HARDLINE_RULES 評分（基準 5.0，向下扣分）

| 維度 | 扣分規則 |
|------|---------|
| 📦 Frontmatter 完整 | 缺 name/description/version/author 任一扣 1.0 |
| 🔤 description ≤60 | 每超 1 字元扣 0.3（最常見錯誤） |
| 🔍 name 格式 | 含大寫/空格/非 hyphen 扣 1.0；>64 字元扣 1.0 |
| 🛠 Hermes-tool framing | 出現 cat/grep/ls/sed/awk 等 shell 工具每處扣 0.5 |
| 📋 段落完整 | 缺任一必要段落扣 0.5 |
| 🚫 禁止詞 | 出現 powerful/seamless/robust 每詞扣 0.5 |
| 📝 author 正確 | author 非 `Hermes` 扣 1.0 |
| 🎯 可重用性 | 內容是一次性對話記錄而非抽象步驟扣 2.0 |
| 🔐 金鑰安全 | 內容含 `sk-`、`cpk-`、`api_key=明文` 等模式扣 3.0（一票否決） |
| 📛 description=name | description 等於 name（去大小寫/標點後）扣 2.0 |

**FINAL_SCORE** = 5.0 - sum(deductions)
**SECURITY_OVERRIDE**：若 🔐 金鑰安全維度扣分 > 0，無論總分多少，一律標記 FAIL，不允許寫入。

**Grade**: A ≥ 4.5 / B ≥ 3.5 / C ≥ 2.5 / D < 2.5

未通過的維度需自動執行一輪修復（最多 2 輪）。

**報告格式**：
```
🌟 FINAL_SCORE / 5.0 — Grade
📦 Frontmatter:  X.X/5.0  🔤 Description:  X.X/5.0
🔍 Name format:  X.X/5.0  🛠 Tool framing:  X.X/5.0
📋 Sections:     X.X/5.0  🚫 Banned words:  X.X/5.0
📝 Author:       X.X/5.0  🎯 Reusability:   X.X/5.0
💡 Fixes needed: ...
```

### R5 — 品質閘門（寫入前執行）

| 閘門 | 檢查 | 通過條件 |
|------|------|---------|
| **G1 Description 長度** | 計算 description 字元數 | ≤60 |
| **G2 Name 格式** | 檢查 name 是否 lowercase-hyphenated | 無大寫/空格/底線 |
| **G3 禁止詞掃描** | 全文掃描禁止詞列表 | 無 powerful/seamless/advanced/robust/comprehensive |
| **G4 Author 正確** | 檢查 author 欄位值 | 等於 `Hermes` |
| **G5 Tool framing** | 全文掃描 cat/grep/ls/sed/awk 並確認非在程式碼區塊內 | 無違規出現 |
| **G6 段落完整性** | 檢查必要段落是否存在 | When to Use + Prerequisites + Procedure + Verification |
| **G7 可重用性** | 內容是否包含具體的檔案路徑/指令而非抽象步驟 | 適用於多種場景而非單一次 |
| **G8 金鑰安全** | 全文掃描 `sk-`、`cpk-`、`api_key=` 等金鑰模式 | 無出現 → 通過；出現 → **FAIL：不允許寫入** |
| **G9 Description 有意義** | 檢查 `description` 是否等於 `name`（去除大小寫與標點差異後比對） | description 不等於 name → 通過 |

未通過的閘門標註 ⚠️，並自動觸發一輪 R4 修復。

### R6 — 寫入與驗證

```bash
# 透過 skill_manage 寫入
skill_manage(action="create", name="skill-name", category="category", content="<SKILL.md content>")

# 或更新
skill_manage(action="patch", name="skill-name", old_string="...", new_string="...")
```

寫入後執行驗證：

```bash
# 確認已建立
skill_view(name="skill-name")
```

### R7 — FEG 極限壓縮（選用）

FEG 壓縮的權威定義位於 **`prompt-factory-7-1/references/feg-core-dsl.md`**（共享參考），此處僅列 SKILL.md 專用的 FEG-L2 格式和 FEG-L3 映射。

當用戶要求 FEG 壓縮時將完整 SKILL.md 壓縮為 DSL：

**FEG-L2（SKILL.md 專用）**：
```
FEG_SKILL[
N:{name}
D:{description ≤60}
V:{version}
T:{tags}
WHEN:{觸發詞濃縮}
RUN:{How-to-Run 濃縮}
PROC:{步驟濃縮}
PIT:{陷阱濃縮}
]
```

**FEG-L3 實例 — HARDLINE_RULES → FEG_CORE_EXTREME 映射**：
```\nFEG_CORE_EXTREME[\nD{FRONT,DESC,NAME,TOOLS,SECT,BAN,AUTH,REUSE,KEY,DNAME};\nS1..5;\nP:FRONT>=5&DESC>=5&NAME>=5&TOOLS>=5&SECT>=5&BAN>=5&AUTH>=5&REUSE>=5&KEY>=5&DNAME>=5;\nR:FRONT<5|DESC<5|NAME<5|TOOLS<5|SECT<5|BAN<5|AUTH<5|REUSE<5|KEY<5|DNAME<5;\nDg:BAN<4&REUSE<4&KEY<4;\nC:TOOLS<3|SECT<3;\nB:KEY<3|BAN<3|REUSE<3|SF|BH|QF;\nM:P>DLV;R>RTY(max=2);Dg>SAFE;C>ASK;B>STOP\n]\n```\n> 維度映射：FRONT=Frontmatter / DESC=description / NAME=name格式 / TOOLS=Hermes-tool / SECT=段落 / BAN=禁止詞 / AUTH=author / REUSE=可重用性 / KEY=金鑰安全 / DNAME=description≠name

FEG 三層級（詳見 `feg-core-dsl.md`）：

| 層級 | 壓縮比 | 說明 |
|------|--------|------|
| FEG-L1 | ~50% | 精簡敘述，去冗詞 |
| FEG-L2 | ~30% | FEG_SKILL DSL 符號化（八區塊濃縮） |
| FEG-L3 | ~15% | FEG_CORE_EXTREME 決策矩陣（含 D/S/P/R/Dg/C/B/M） |

### R8 — 技能迭代流程（更新既有技能）

當用戶要求「更新技能 X 的 Y 部分」而非從頭建立時，使用此流程：

**Step 1: 讀取現有技能**
```bash
skill_view(name="target-skill")
```

**Step 2: 判斷更新模式**
| 模式 | 適用情境 | 工具 | 版本變更 |
|:-----|:--------|:-----|:--------:|
| **修正** | 修復錯誤、更新過時指令 | `skill_manage(action='patch')` | +0.0.1 |
| **擴展** | 新增步驟、規則或參考 | `skill_manage(action='patch')` 或重建 procedures 段落 | +0.1.0 |
| **重構** | 大幅改寫結構或邏輯 | `skill_manage(action='edit')`（提供完整新內容） | +1.0.0 |

**Step 3: 執行變更**
- 修正/擴展：用 `patch` 精準修改，保護未變動部分
- 重構：確保新版本仍通過 HARDLINE_RULES 評分 ≥4.5

**Step 4: 版本更新**
更新 frontmatter `version` 欄位（根據變更幅度）：
```
修正：0.1.0 → 0.1.1
擴展：0.1.0 → 0.2.0
重構：0.1.0 → 1.0.0
```

**Step 5: 驗證**
```bash
skill_view(name="target-skill")  # 確認變更生效
# 重新執行 HARDLINE_RULES 評分
```

**迭代陷阱**：
- 不要用 `skill_manage(action='edit')` 做小修改（會覆蓋整個檔案）。原則：>30% 內容變動才用 edit，<30% 用 patch。
- 更新後務必重新驗證 FEG 壓縮是否仍正確對應新內容。
- 若技能有互補技能（如 memory-policy ↔ memory-compression），更新一方後檢查另一方是否需要同步調整。

### R9 — 技能腳本與 Cronjob 模式

技能配上 `scripts/` 腳本 + `cronjob` 工具時，需考慮 Cron 執行環境的限制。

**核心規則**：Cron job 在非互動 shell 中執行，**不 source `.bashrc` / `.profile`**。若腳本需要 API 金鑰，使用 `get_env_from_bashrc()` 模式：

```python
def get_env_from_bashrc(var_name):
    import re
    try:
        with open(f"{__import__('os').path.expanduser('~')}/.bashrc") as f:
            for line in f:
                m = re.match(rf'\s*export\s+{var_name}=["\']?(.+?)["\']?\s*$', line)
                if m: return m.group(1)
    except: pass
    return ""
```

**watchdog 模式（no_agent=True）**：
- 對於純資料收集/門檻檢查（非 LLM 推理需求），使用 `no_agent=True`
- 腳本 stdout 直接作為 cron 交付內容 — 設計腳本使輸出直接可讀
- 腳本 stdout 為空 = 無變化 = 不發送（靜默模式）
- 適合：API 端點存活檢查、磁碟/記憶體用量、rate limit 監控、變更偵測

**輕量監控偏好**：當用戶要求監控/狀態檢查，優先選擇 `no_agent=True` cron + 腳本，而非獨立技能。省 tokens、省 LLM 調用、交付更即時。

| 模式 | 適用 | 優點 |
|:-----|:-----|:-----|
| `no_agent=True` + script | 純檢查、純監控 | 零 token 消耗、即時交付 |
| `no_agent=False` + prompt | 需推理（摘要、篩選、判斷） | LLM 可分析後再報告 |

**迭代陷阱**：
- Cron 腳本放置於 `~/.hermes/scripts/`，透過 `cronjob(script="filename.py")` 引用，**不可用絕對路徑**。
- 腳本失敗時 cron 會自動報告錯誤 — 不需要手動處理 `try/except` 的 fallback 訊息（除非要優雅的降級提示）。

### R10 — 敏感技能加密模式

當技能內容涉及安全架構（注入防禦、偵測邏輯、繞過手法等），不應以明文推上公開 repo。使用 GPG 雙檔策略：

```
remote (GitHub):          SKILL.md.gpg     ← AES256 加密
local (~/.hermes/skills/): 
  SKILL.md                ← 解密後明文，被 .gitignore 排除
  SKILL.md.gpg            ← 同步 remote，還原源
```

**執行流程：**

```bash
# 1. 建立技能（明文 SKILL.md）
skill_manage(action="create", name="skill-name", content="...")

# 2. 生成金鑰並加密
KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
gpg --symmetric --batch --passphrase "$KEY" --cipher-algo AES256 \
  --output SKILL.md.gpg SKILL.md

# 3. 金鑰存入 env（.gitignore 會排除）
echo "SKILL_DECRYPT_KEY=$KEY" >> ~/.hermes/env/<skill-name>.key
chmod 600 ~/.hermes/env/<skill-name>.key

# 4. 明文加入 .gitignore
echo "security/<skill-name>/SKILL.md" >> .gitignore

# 5. 推 .gpg 上 remote，金鑰留在本機
git add security/<skill-name>/SKILL.md.gpg .gitignore
git commit -m "feat: add <skill-name> skill (encrypted)"
```

**注意**：金鑰是本機的單點故障。建議另備份至 GCP Secret Manager 或 age 加密後存離線媒介。

| 安全原則 | 實作 |
|:---------|:------|
| remote 永不存明文 | ✅ 只推 SKILL.md.gpg |
| 金鑰不進 git | ✅ env/ 在 .gitignore |
| Hermes 可載入 | ✅ 本機留 SKILL.md（被 gitignore） |
| 可還原 | ✅ 本機 .gpg 副本作為 restore point |

## Pitfalls

- **description 是最大陷阱**：這是最常違規的規則。每次寫入前必須用 G1 確認 ≤60 字元。
- **description = name 是批量匯入留下的通病**：從外部系統（Copilot prompts、知識庫）大量匯入技能時，易留下 frontmatter description = 技能名稱的缺陷。2026-07-07 審計發現 75/120 技能有此問題。建立技能後務必用 G9 確認；批量修復方式見 `references/bulk-description-fix.md`。
- **author 不可從環境讀取**：永遠寫 `Hermes`。不要從 `whoami`、git config、或 OS username 取得。
- **FEG 壓縮不可破壞 SKILL.md 結構**：壓縮版僅供快速參照，不可作為寫入 skill_manage 的內容。
- **不要寫 router/index hub skill**：hub skill 只指向其他 skill 是無效的。
- **過大的 scripts 要分離**：超過 30 行的 Python/Shell 腳本應獨立為 `scripts/` 檔案，用 `skill_manage(action='write_file')` 寫入。
- **從既有技能學習**：建立前先用 `skill_view` 查看結構相似的技能（特別是 `prompt-factory-7-1` 和 `strat-*` 系列），避免重複造輪子或自創不一致的命名/格式。
- **跨技能 FEG 一致性**：若新技能使用 FEG 壓縮，必須引用 `prompt-factory-7-1/references/feg-core-dsl.md` 作為共享參考，不允許獨立定義 FEG 語法。
- **金鑰禁止嵌入技能內容**：API 金鑰 (`sk-`、`cpk-` 等) **永遠不允許**寫在 SKILL.md 中。改用模組化 `.env` 模式：金鑰存於 `~/.hermes/env/{provider}.env`，腳本從該路徑讀取。`.bashrc` 統一 source 全部。金鑰檔案不得進入 git repo。
- **Script 分離 + 金鑰路徑**：技能若附帶 Python 腳本，必須從 `~/.hermes/env/` 讀取金鑰（透過讀取對應 `.env` 檔案），不可硬編碼或從 `os.environ` 直接依賴，後者在 cron 環境中不 work。
- **內容萃取而非原文搬運**：當技能素材來自外部文件（小說、推演研究、長篇報告、超長網頁等），只萃取其**邏輯架構與映射關係**，不將原文段落大段貼入 SKILL.md。技能是「怎麼做」的指引，不是「原文是什麼」的存檔。用戶曾明確糾正：「你不能把整個提示放上去，你要去把它純邏輯。」
- **加密技能的金鑰管理**：使用 R10 加密模式時，金鑰以 `~/.hermes/env/<name>.key` 存放。這是單點故障。建議立即備一份至 GCP Secret Manager，或至少確認 `.gitignore` 有排除該金鑰檔。

## Verification

```bash
# 確認 skill 可用
skills_list | grep "skill-name"

# 確認 frontmatter 正確
skill_view(name="skill-name")  # 檢查 description 長度
```
