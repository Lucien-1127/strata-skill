# Strata Skill — Hermes Agent 技能庫

Strata Skill 是為 **Hermes Agent** 量身打造的技能庫，收錄 139 項技能、涵蓋 16 大分類，涵蓋提示詞工程、開發維運、法律應用、策略分析等領域。讓你的 Hermes Agent 一鍵獲得專業能力。

---

## 技能分類一覽

| 分類 | 說明 | 技能數量 |
|------|------|----------|
| **automation** | 自動化作業（Canva、排程等） | 1 |
| **communication** | 溝通風格與回應慣例 | 1 |
| **devops** | 開發維運、診斷、部署、監控 | 16 |
| **hermes** | Hermes 自我進化與技能管理 | 3 |
| **legal** | 台灣法律文件與合約範本 | 2 |
| **maintenance** | 系統維護與更新程序 | 1 |
| **pdf** | PDF 文件生成（含 CJK 支援） | 1 |
| **prompt-engineering** | 提示詞工程（圖像/影片） | 2 |
| **quality** | 程式品質與 API 驗證 | 2 |
| **research** | API 研究、法律研究、GitHub 深度分析 | 4 |
| **security** | 提示詞注入防禦框架 | 1 |
| **strategy** | 策略分析、任務規劃、FEG 架構 | 13 |
| **system** | 系統層約束與規則 | 1 |
| **system-admin** | 系統管理與基礎設施 | 2 |
| **video** | 影片流水線與提示詞工作流 | 1 |
| **writing** | 寫作指令編譯與內容生成 | 1 |

### 各分類詳細技能

#### automation
- `canva-automation` — Canva Connect API 自動化（設計/資產/匯出/自動填充）

#### communication
- `user-communication-style` — 老闆偏好的回應格式、語言風格與溝通慣例

#### devops
- `api-route-diagnostics` — FastAPI 路由層智慧診斷與修復
- `backend-api-diagnostics` — 後端 API 服務路由層診斷與修復
- `canva-connect` — Canva Connect API 整合（OAuth、設計操作）
- `fastapi-diagnosis` — 系統化 FastAPI 路由診斷
- `fastapi-routing-diagnosis` — FastAPI 路由診斷、最小修改、迴歸驗證
- `fastapi-routing-diagnostics` — FastAPI 路由診斷與修復 SOP
- `gcp-vm-administration` — GCP VM 狀態管理與驗證
- `git-sync-workflow` — 本地 Git repo 與遠端同步
- `hermes-proxy-console` — Hermes Proxy 監控 Mini App
- `managing-hermes-legal-system` — 智研法律系統管理程序
- `mini-app-deployment` — Mini App 完整部署工作流
- `segmentio-stack-ecs` — AWS ECS 基礎設施佈建（Terraform）
- `selfhost-hermes-web-tool` — Hermes Web Dashboard 自架
- `server-watchdog` — 伺服器程序 Watchdog（cronjob）
- `web-service-deploy` — 網頁服務完整生命週期部署
- `zhiyan-system-health-audit` — 智研記憶與儲存健康審計

#### hermes
- `hermes-self-evolution` — 自動進化 Hermes 技能與提示詞
- `hermes-skill-author` — SKILL.md 品質評分撰寫
- `hermes-skill-forge` — 將重複任務自動轉為可重用技能

#### legal
- `contract-templates` — 台灣實務合約範本庫
- `taiwan-legal-document-formatting` — 法院/政府文件格式規則

#### maintenance
- `zhiyan-system-update` — 智研法律系統更新程序

#### pdf
- `fpdf2-cjk-pdf-generation` — 使用 fpdf2 產生 CJK PDF（無重疊）

#### prompt-engineering
- `agnes-prompt-architect` — Agnes 圖像+影片統一提示詞架構
- `img2vid-character` — 圖生影角色一致性提示詞架構

#### quality
- `fastapi-route-diagnosis` — 假設驅動 FastAPI 路由診斷
- `runtime-api-verification` — API 變更後自動端點驗證

#### research
- `api-integration-research` — 第三方 API 系統性研究方法
- `deep-research-github-repo` — GitHub 儲存庫架構深度分析
- `taiwan-legal-research` — 台灣法律主題系統性研究
- `verification-before-completion` — 完成前驗證流程

#### security
- `keter-prompt-defense` — 多層次提示詞注入防禦框架

#### strategy
- `architecture-reimagining` — 架構重構分析（7 步驟）
- `decision-graph-router` — FEG 風格決策路由
- `dispatching-parallel-agents` — 並行代理任務分派
- `executing-plans` — 書面實作計劃執行
- `feg-state-hook-architecture` — FEG/State Machine/Hook 模式嵌入
- `strat-anchor-5d` — 脈絡錨定 + 5 維分析
- `strat-drill` — 邏輯壓力測試與邊界案例
- `strat-forge-output` — 最終輸出鍛造與格式規範
- `strat-memory-policy` — 跨對話記憶壓縮規則
- `strat-orchestrator` — 策略模組協調分派
- `strata-memory-compression` — STRATA 記憶壓縮模式
- `subagent-driven-development` — 子代理驅動開發
- `writing-plans` — 規格說明轉多步驟實作計劃

#### system
- `iron-laws` — 三條鐵律（所有 Agent 行為最高約束）

#### system-admin
- `zhiyan-rag-infra` — 法律文件語意向量搜尋基礎設施
- `zhiyan-vm-setup` — 智研法律系統 VM 設定

#### video
- `idol-video-pipeline` — 角色參考圖→影片流水線（四階段審核）

#### writing
- `writer-compiler` — 動態多領域寫手指令編譯器

---

## 安裝方式

### 前置需求

- [Hermes Agent](https://hermes-agent.nousresearch.com) 已安裝並可正常執行
- Git

### 1. Clone 儲存庫

```bash
git clone git@github.com:Lucien-1127/strata-skill.git ~/.hermes/skills/
```

### 2. 連結技能

```bash
hermes skill link ~/.hermes/skills/
```

### 3. 驗證安裝

```bash
hermes skills list | head -20
```

看到技能清單即表示安裝成功。

---

## 如何貢獻

我們歡迎任何形式的貢獻！請遵循以下流程：

1. **Fork** 此儲存庫
2. 建立您的功能分支：`git checkout -b feature/my-awesome-skill`
3. 撰寫或修改技能（每個技能為一個獨立目錄，內含 `SKILL.md`）
4. 確保您的技能包含：
   - `SKILL.md` 格式正確（YAML frontmatter + Markdown 內文）
   - 清晰的觸發條件與使用說明
   - 驗證步驟（如適用）
5. 提交 Pull Request 至 `master` 分支

### PR 規範

- PR 標題請簡潔描述變更內容
- 說明新增/修改的技能用途與觸發條件
- 確保不含任何 API Key、Token、密碼或環境路徑
- 若為新技能，請在 README 對應分類中補上描述

---

## 授權條款

本專案採用 MIT License — 詳見 [LICENSE](./LICENSE) 檔案。
