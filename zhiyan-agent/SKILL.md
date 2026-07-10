---
name: zhiyan-agent
description: "智研法律 AI Agent 系統設定"
status: stable
---

# zhiyan-agent

## 📖 Description

智研法律 AI Agent 系統設定

---

# 🤖 智令Agent

## 功用
智研法律的 AI Agent 系統提示詞設定，包含法律諮詢、文件分析與案件管理。

## 來源
原檔: copilot/system-prompts/智研Agent.md

## 適用
法律相關任務引用此 skill 時載入對應系統提示詞。

## 🏗️ 系統架構概覽

智研 AI 法律系統採用 **動態多層規格拼接架構 (Dynamic Layer Composing Architecture)**，透過階層式規格文件動態組裝生成上下文提示詞，實現精準的法律推理與幻覺防護。

### 三層架構結構

#### 1️⃣ 核心控制層（必載）
- `09_AGENT_SYSTEM_PROMPT_v1.0.0.md` - 基本系統提示詞
- `10_主人格_MASTER_v2.0.0.md` - 智研核心人格定義
- `11_啟動流程_BOOT_v2.40.0.md` - LLM 啟動思考流程
- `12_核心閘門_CORE_GATE_v1.1.0.md` - **事實閘門**（本次重點強化）
- `13_空間核心規格_PPL_SPACE_CORE_v3.0.0.md` - 內部工作空間規格
- `14_智研AI代理運行流程_RUNBOOK_v1.0.0.md` - **代理執行 runbook**：啟動順序（L0→L5）、任務路由對照表（8 種任務類型）、7 個常見代理問題與解法、輸出前 6 項檢查清單、維運原則。*📎 參考：`references/zhiyan-runbook.md`*
- `15_任務路由表_TASK_ROUTER_v1.0.0.md` - 動態任務分發
- `17_子代理並行策略.md` - **五種並行加速模式**：法庭模擬三方並行（🔥 加速 ×3）、引證驗證搜尋並行（🟡 加速 ×3）、TYPE-S QA 分離防 Blind Spot（🟡）、多法域平行研究（🟢）、RAG+聯網平行抓取（🟢）。含 Hermes `delegate_task` 實作範例。*📎 參考：`references/subagent-parallel-strategy.md`*

#### 2️⃣ 模式與引用層（品質防護）
- `20_模式_REPORT_報告_v2.0.0.md` - 報告格式規範
- `21_模式_RESEARCH_研究_v2.0.0.md` - 研究方法論標準
- `22_模式_QC_查核_v2.0.1.md` - 品質檢查模板
- `30_引用政策_CITATION_POLICY_v2.2.0.md` - **引用鐵律**（含 C5.4 分級對應規則）
- `31_引用升級手冊_v2.0.0.md` - 引用政策優化指南
- `32_引用政策優化完成手冊_v2.0.0.md` - 引用政策執行範例

#### 3️⃣ 模組與人格層（按需載入）
- 依 `15_任務路由表` 動態選擇：
  - `40_模組_訴訟策略_v2.2.0.md` - 訴訟攻防防護
  - `41_模組_安全風險對話處理_v1.0.0.md` - 安全檢測前置
  - `43_模組_法庭模擬_v1.1.0.md` - 法庭角色扮演
  - `44_模組_申論題測試_v1.0.0.md` - 申論題評分框架
  - `46_人格_申論寫作_WRITER_v1.0.0.md` - 申論寫作人格
  - `47_模式_提示詞工程師_PROMPT_ENGINEER_v1.0.0.md` - 提示詞設計支援
  - `48_人格_法律書狀師_LEGAL_WRITER_v1.0.0.md` - 法律文書撰寫
  - `49_模組_合約風險策略_CONTRACT_RISK_v1.0.0.md` - 合規風險評估
  - `50_人格_顧問_v1.1.0.md` - 法律顧問諮詢
  - `51_人格_助教批改_v1.2.0.md` - **申論題批評助教**
  - `52_人格_教學_v1.1.0.md` - 法律教學人格
  - `53_人格_總綱_v2.0.0.md` - 綜合法律分析

## 🔧 相關專案

- **zhiyan-search** (`/home/ysga1/zhiyan-search/`) — docs/ 語意向量搜尋。ChromaDB + BAAI/bge-m3 embedding（經由 freely 本地代理或直接 HF Inference API）。`python build_index.py` 建索引、`python search.py` 查詢。詳見下方**向量索引建置**流程。

### 向量索引建置 (`build_index.py`)

**自動同步 cronjob** 🆕：`zhiyan-search 索引自動同步`（ID: `dfc335982be7`，每 4h，watchdog 模式）
- 腳本：`~/.hermes/scripts/auto-index.py`（`no_agent=True`）
- 偵測 git log docs/ 變更 → 確保 freely proxy 在線 → 執行增量建置
- 無變更時完全靜默，有變更才報告
- 強制重建：`python3 ~/.hermes/scripts/auto-index.py --force`
- 檢視狀態：`python3 ~/.hermes/scripts/auto-index.py --status`

**三種 Embedding 途徑（依優先順序）**：

| 途徑 | 服務 | 模型 | 埠 | 說明 |
|------|------|------|-----|------|
| 🥇 freely 代理 | `freely.py` (本機) | BAAI/bge-m3 | 8008 | HF Inference API 包成 OpenAI-compatible，推薦 |
| 🥈 HF 直連 | HuggingFace InferenceClient | BAAI/bge-m3 | — | 無須代理，但 API 可能 502/限流 |
| ❌ FreeLLM | `localhost:3001/v1` | text-embedding-3-small | 3001 | 上游 GitHub 頻繁 429，不建議 |

**標準建置流程**：

```bash
# 1. 啟動 freely 代理（如未執行）
cd /home/ysga1/zhiyan-search && python3 freely.py &
sleep 2
curl -s http://localhost:8008/health  # 確認回傳 {"status":"ok"}

# 2. 確保 config.yaml 指向 localhost:8008/v1
# 3. 清理舊索引後建置
cd /home/ysga1/zhiyan-search
python3 -c "import shutil, os; shutil.rmtree('vector_store', ignore_errors=True); os.makedirs('vector_store'); print('ready')"
python build_index.py
```

**常見失敗模式與解決方案**：

- **HF Inference API 502 / 429** → 重試即可；改用 freely 代理可降低頻率
- **ChromaDB「readonly database」** → ChromaDB 1.5.9 Rust bindings 在多批次 `collection.add()` 後可能鎖定資料庫。**解法**：修改 `build_index.py` 收集所有 chunks 後一次性寫入（已預設套用此模式）
- **config.yaml 被自動還原** → 可能是另一個並行 Hermes 子代理同時執行 `build_index.py`。用 `ps aux | grep build_index` 檢查衝突程序後 `kill` 再執行
- **`build_index.py` UnboundLocalError: `model` 未定義** — 當所有 .md 檔案因 hash 不變而被跳過時，`model` 變數僅在 `for filepath` 迴圈內定義，未被執行到的話結尾 summary 列印會炸 `UnboundLocalError`。**解法**：在迴圈前加上 `model = cfg["embedding_model"]`，移除迴圈內的重複賦值

**驗證**：
```bash
ls -la vector_store/                                  # 確認存在 chroma.sqlite3
python3 -c "import chromadb; c=chromadb.PersistentClient(path='./vector_store/'); print(c.get_collection('zhiyan_docs').count())"  # 應 > 0
```

## 🔐 幻覺防護機制

系統透過 **「核心閘門 → 引用政策」雙層驗證閉環** 防止法律幻覺：

### 第一道防線：核心閘門 (`12_核心閘門_CORE_GATE_v1.1.0.md`)
- 對輸入事實進行六級分類：`[VERIFIED]` / `[CROSS_REFERENCED]` / `[USER_REPORTED]` / `[NEED_CHECK]` / `[局部不明]` / `[A/B/C 高風險]`
- 強制規則：違反者系統立即中止並回溯

### 第二道防線：引用政策 (`30_引用政策_CITATION_POLICY_v2.2.0.md`)
- **條號存在性驗證**：台灣民法 §1–§1225 範圍硬邊界
- **已刪除條文處理**：§987、§991、§992 等已知廢止條文
- **引用策略**：T1(本地白話RAG) → [1](全國法規) → [2](判決書) → [3](學術論文)
- **C5.4 來源可信度分級對應規則**：將核心閘門六級分類映射為強制輸出行為

### 🔗 關聯：來源驗證閘門（外部技能引用）

本系統的來源驗證閘門定義於外部技能 `taiwan-legal-research` 的 **Phase S0**，為法律研究的強制前置步驟。執行法律相關任務時，**必須在引用任何來源之前** 調用該閘門：

- **法條條號** → `taiwan-legal-research` Phase S0.1：`curl` 抓取全國法規資料庫原文驗證
- **判決字號** → `taiwan-legal-research` Phase S0.2：Wikipedia API 或間接來源驗證字號完整性
- **學說引用** → `taiwan-legal-research` Phase S0.3：格式分離，不得掛在法條引用下
- **強制執行** → `taiwan-legal-research` Phase S0.4：未通過閘門的引用不得出現在最終報告

**遵守方式**：
1. 在 Phase 0a（並行派發子代理）的任務約束中，為每個法務子代理傳入「必須執行 curl 原文驗證」的指令
2. 最終報告的 `【本段資料來源】` 區塊中，若來源為第 T2 層（判決書）或第 T3 層（學術論文），必須附註驗證狀態（`已驗證` / `因系統限制僅間接驗證`）

## 📄 文件輸出

本 skill 的 PDF 生成職責由 `taiwan-legal-document-formatting` 專責。**不再使用 fpdf2 直出 PDF**，統一走 Word 管線。

### 生成管線（強制流程 — 8 步驟，不可跳過）

```
載入 taiwan-legal-document-formatting（選軌道：法院/政府/合約）
  ↓ python-docx（防孤行：widow_control + keepLines + keepNext）
output.docx
  ↓ libreoffice --headless --convert-to pdf
output.pdf
  ↓ bash 驗證（pdfinfo 頁數 + pdffonts 字型嵌入 + ls 檔案大小）
  ↓ QA 閘門 — 並行派發 2 子代理：
     ├── 子代理 A：排版檢查（字型/邊距/孤行/切頁/空白頁）
     └── 子代理 B：引用檢查（判決字號/學說標籤/函釋格式/G3統一度）
  ↓ 彙整結果
     ├── 全部 ✅ → 交付檔案到使用者對話
     └── 有 ❌ → 修正 → 重新生成 → 重新 QA
  ↓ 確認使用者已收到（若沒收到 → 立即補發，不辯解）
```

### 儲存位置

| 文件類型 | 存放位置 |
|:---------|:---------|
| 法律分析報告/PDF | `zhiyan-legal/docs/80_技術參考/` |
| 技能檔 | `strata-skill (~/.hermes/skills/)` |
| ❌ 不要存 | `/home/ysga1/` 根目錄 |

### 法律報告品質標準（2026-07-07 審計結論）

| 項目 | 標準 | 最低分數 |
|:-----|:------|:--------:|
| 法條引用 | 條號正確、引用現行條文 | 9/10 |
| 判決字號 | 每章至少 3~5 則最高法院/高院判決 | 7/10 |
| 學說引用 | 引用王澤鑑、謝在全、黃茂榮等 | 7/10 |
| 函釋引用 | 內政部地政司相關函文 | 7/10 |
| 客觀中立 | 用「可能」「涉及」「依個案判斷」，不用「一定違法」 | 9/10 |
| 引用格式 | G3 ^[來源簡稱] + 章末【本段資料來源】 | ✅ |

### 陷阱

- ❌ **判決無字號**：只寫「相關判決」等同不可查證。至少補字號或降級措辭。
- ❌ **學說掛法條引用**：學說歸學說（^[學說見解]），法條歸法條（^[全國法規資料庫]）。
- ❌ **MOICA/MOEA 混淆**：`moea`(經濟部) vs `moica`(內政部)。行動憑證是 `fido.moi.gov.tw`。
- ❌ **證交法§20/§171 刑度混亂**：§20 無刑罰，違反者歸 §171（3~10 年）。
- ❌ **孤立引用**：每個 `^[來源]` 必須在當章 `【本段資料來源】` 中有對應條目。
- ❌ **報告存錯 repo**：法律分析報告 → zhiyan-legal/docs/。技能 → strata-skill。hermes-skills 是另一個。
- ❌ **PDF 段落切頁未檢查** — DOCX→PDF 後必須用 pdfinfo/pdftotext 確認段落不被不合理切分（標題孤行在頁尾、判決從中間切開）。生成時對標題設 keep_with_next，全文設 widow_control，重要段落加 w:keepLines/w:keepNext。
- ❌ **檔案存好後忘記發送給使用者** — 產出歸檔後必須在當下回應中送達使用者對話視窗，不 能只存路徑。發送後主動確認是否收到。
- ❌ **用 text_to_speech 傳送非音訊檔案** — text_to_speech 會把檔案轉語音。PDF 必須直接用平台檔案傳輸機制。

## 🧪 驗證與測試

### C5.4 驗證測試腳本
- 位置：`tests/test_c54_validation.py`
- 說明：驗證 C5.4 來源可信度分級對應規則在實際 LLM 執行中的效果
- 測試案例：5 案例涵蓋 NEED_CHECK / A類高風險 / USER_REPORTED 等情境
- 相關文件：`references/c54-validation-test.md`

## ⚙️ 系統維護紀錄

### 磁碟擴容（2026-07-04）
- 附加 10GB 永久磁碟至 `/mnt/data`
- 透過 `/etc/fstab` 實現開機自動掛載

### Swap 啟用（2026-07-04）
- 2GB swap 於 `/mnt/data/swapfile`（600 權限）
- 寫入 `/etc/fstab` 實現開機自動掛載

### 字體與排版基礎設施（2026-07-06）
- 安裝 `fonts-noto-cjk`（Noto Serif CJK TC + Noto Sans CJK TC）
- 安裝 `libreoffice-writer-nogui`（TLDS DOCX→PDF 轉換管線）
- 建立 `references/legal-doc-pdf-generation.md` 完整 PDF 生成模板
- TLDS 規格參照：`/home/ysga1/zhiyan-legal/docs/80_技術參考/TLDS-v1.0.0.md`

## 🖥️ 執行環境

- **平台**: GCP VM (`zhiyan-prod`, `us-west1-a`)
- **作業系統**: Ubuntu 24.04 LTS
- **規格**: 2 vCPU, 8GB RAM, 50GB + 10GB 磁碟
- **使用者**: `ysga1`

## 📚 相關文件

- `references/gcp-attach-disk.md` - GCP 磁碟附加與掛載指南
- `references/c54-validation-test.md` - C5.4 驗證測試說明
- `references/zhiyan-runbook.md` - 代理運行流程 RUNBOOK（啟動順序、任務路由對照、常見問題與維運原則）
- `references/legal-deep-research.md` - 法律議題深度研究 + 風險評估方法論（三步驟拆解、delegate_task 平行分派、結果整合格式）
- `references/subagent-parallel-strategy.md` - 子代理並行策略（五種並行模式 + Hermes delegate_task 實作）
- `references/legal-doc-pdf-generation.md` — PDF 生成完整模板（fpdf2 歷史參考 + 現行 Word 管線 SOP 指針）
- `references/vector-index-build.md` - 向量索引建置流程、失敗模式與修復記錄（2026-07-06）
- `references/backend-server-maintenance.md` — 後端 API Server 維護指南（2026-07-09）：完整路由表、L1/L2/L3 診斷流程、alias 修復模式、常見故障對照、Provider 路由表

## 🛠 排版腳本

- `scripts/legal-analysis-pdf-template.py` - 法律分析 PDF 樣版腳本（含 section/sub_item/check_space/law_box/table 輔助函數 + 跨頁斷層防護 + 末頁填補）

## 🔄 最近更新

- **2026-07-07**：生成管線更新為 8 步驟 SOP（python-docx防孤行 → LibreOffice → bash驗證 → QA雙子代理 → 交付/修正）。新增 3 條陷阱（切頁/檔案發送/音訊繞道）。