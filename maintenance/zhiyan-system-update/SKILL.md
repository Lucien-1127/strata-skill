---
name: zhiyan-system-update
description: Procedure for updating the Zhiyan AI Legal System on a GCP VM, including applying patches to citation policy, fixing G3引用格式, updating task router, and optionally creating swap.
category: maintenance
---

# Zhiyan AI Legal System Update Procedure

## Trigger Conditions
- When instructed to apply updates to the Zhiyan AI Legal System on a GCP VM.
- After receiving a directive to fix G3引用格式 or update task router mappings.
- When the system needs swap space configured for safety.
- When the user requests removal of citation markers for improved readability (e.g., to avoid interference with copy-paste from external sources).
- When updating to the latest citation format (superscript style) and task router mappings.

## Steps

### 1. Ensure swap space (if needed)
- Check current swap: `swapon --show`
- If none, create a 2GB swap file on the data disk:
  ```bash
  sudo fallocate -l 2G /mnt/data/swapfile
  sudo chmod 600 /mnt/data/swapfile
  sudo mkswap /mnt/data/swapfile
  sudo swapon /mnt/data/swapfile
  echo '/mnt/data/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- Verify: `swapon --show` and `free -h`

### 2. Fix G3引用格式 (SPACE_CORE) to use superscript format
- Open the file: `docs/10_核心控制層/13_空間核心規格_PPL_SPACE_CORE_v3.0.0.md`
- Locate the G3 line under 【GLOBAL_RULES — 鐵律】.
- Replace the line:
  ```
  || **G3. 引用格式** | 統一使用 [1][2][3]…（v2.0 格式，已驗證） ||
  ```
  with:
  ```
  || **G3. 引用格式** | 正文句尾用：^[來源簡稱]（例：^[民法§184]、^[判決字號]、^[契約書.pdf]） ||
  ```
- Update the version number in the frontmatter from `v3.00_HYBRID` or `v3.01_HYBRID` to `v3.02_HYBRID` and update the 建立日期 to current date.
- Update the 說明 under 【融合優化版】 to reflect the new version.
- Commit the change with message: `fix(G3): 統一引用格式為 ^[來源簡稱]，禁用舊式 [1][2]… — SPACE_CORE v3.02`

### 3. Update Citation Policy (CITATION_POLICY) to v2.3
- Open: `docs/20_模式與引用層/30_引用政策_CITATION_POLICY_v2.0.0.md`
- Update the version in the frontmatter from `v2.2` to `v2.3` and update the 最後更新日期.
- Update the 變更內容 to: `v2.2 → v2.3：引用格式統一為句尾上標+末尾清單`
- In the 版本管理 table, add a new row:
  ```
  | v2.3 | 2026-07-05 | 引用格式統一為句尾上標+末尾清單 |
  ```
- Update the 引用方式 sections in C4.1, C4.2, and C4.3 to use superscript format:
  - For C4.1 MODE_QC: change `- 每個「依據」項後加 、…` to `- 每個「依據」項後加 ^[來源簡稱]…`
  - For C4.2 MODE_RESEARCH: similarly change `- 重點敘述部分加 [數字]` to `- 重點敘述部分加 ^[來源簡稱]…`
  - For C4.3 MODE_REPORT: similarly change `- 每個「依據」段落落尾標註 [1][2]…` to `- 每個「依據」段落落尾標註 ^[來源簡稱]…`
- Update the C2.1 段落末尾引用表 to show the new format:
  ```
  【本段資料來源】
  ^[來源簡稱1]
  ^[來源簡稱2]
  ^[來源簡稱3]
  ```
- Update the C2.2 完整段落引用表示例 to use the new format:
  **段落內容：**
  > 人工智能正在改變產業結構。根據 2024 年調查^[1]，89% 的企業已導入 AI 工具^[2]。專家預測未來五年將有 40% 的工作角色轉變^[3]。
  **段落末尾標註：**
  ```
  【本段資料來源】
  ^[1] 2024 AI Adoption Report — https://example.com/ai-report-2024
  ^[2] McKinsey Global AI Survey 2024 — https://example.com/mckinsey-ai-2024
  ^[3] World Economic Forum Future of Jobs Report — https://example.com/wef-jobs-2024
  ```
- Update the C8 常見問題與範例 to reflect the new format:
  - For Q: 同一段落引用多個來源，怎麼標註？ change the example to use ^[來源] format.
  - For Q: 能否在文中插入超連結而非數字標記？ update the reasoning to reflect that superscript is preferred over hyperlinks for readability.
- Update the C7 品質檢查清單內容:
  - Change `inline 標記` row from `第一次引用才加 [數字]，後續重複不加` to `第一次引用才加 ^[來源簡稱]，後續重複不加`
- Commit the change with message: `refactor(citation): 統一格式為句尾上標+末尾清單 — v2.3.0`

### 4. Update Task Router (TASK_ROUTER) to v1.1.0
- Open: `docs/10_核心控制層/15_任務路由表_TASK_ROUTER_v1.0.0.md`
- Change the title in the frontmatter and heading to `v1.1.0`.
- In the 快速路由表, add two rows after the ESSAY_TEST row:
  ```markdown
  || 契約審查、合約風險、合約條款、違約責任 | CONTRACT_RISK | `49_模組_合約風險策略_CONTRACT_RISK_v1.0.0.md` ||
  || 法律書狀、起草書狀、民事起訴狀、刑事上訴書、答辯狀 | LEGAL_WRITER | `48_人格_法律書狀師_LEGAL_WRITER_v1.0.0.md` ||
  ```
- In the 衝突處理 section, add two new rows:
  ```markdown
  || R-申論仲裁 | 若同時觸發 TA_REVIEW 與 ESSAY_TEST → 偵測到「批改」「評分」「幾分」「哪裡錯」→ 導向 TA_REVIEW；偵測到「出題」「考我」「練習」「測試」→ 導向 ESSAY_TEST；兩者皆無 → 追問：「您是要批改一份答案，還是想讓我出題考您？」 ||
  || R-開庭仲裁 | 若同時觸發 LITIGATION 與 COURTROOM → 偵測到「模擬」「演練」「角色扮演」「扮演法官/律師」→ 導向 COURTROOM；否則一律導向 LITIGATION（真實訴訟優先原則） ||
  ```
- Update the version number in the frontmatter and heading to `v1.1.0`.
- Commit with message: `feat(TASK_ROUTER): 新增 CONTRACT_RISK/LEGAL_WRITER 映射，補充申論/開庭仲裁規則 v1.1.0`

### 5. Remove temporary citation markers (if any remain from previous formats)
- The user prefers that documentation files do not contain citation markers that interfere with readability and copy-paste from external sources. The final format uses superscript markers like ^[來源簡稱] which are less intrusive.
- After making other changes, ensure that any legacy `[digit]` patterns are removed from the documentation files (except in code blocks or intentional examples where they are meaningful). This can be done with a command like:
  ```bash
  find . -name "*.md" -not -path "*/.git/*" -exec sed -i 's/\[\d\+\]//g' {} +
  ```
  (Exercise caution: verify that it does not affect code or data that legitimately uses such patterns.)
- Commit the change with message: `chore: cleanup legacy [1][2] citation markers`

### 6. Verify changes
- Run `git status` to confirm modified files.
- Run `git push origin main` to push to remote.
- Optionally, run the system tests to ensure nothing broke.
- Verify that the citation format is correct: check that inline citations appear as ^[來源簡稱] and that the source lists are present.
- Confirm that no unwanted `[1][2]` patterns remain in the documentation files (except in code blocks or intentional examples).

## Pitfalls
- Forgetting to update the version number in the frontmatter may cause version confusion.
- When editing tables in markdown, ensure the pipe alignment remains correct; otherwise the table may render incorrectly.
- The swap file must be created with correct permissions (600) to be secure.
- After changing SPACE_CORE, ensure any dependent components are aware of the G3 change (though it is a comment/rule, not code).
- When removing citation markers, ensure that you do not inadvertently remove markers from code blocks, data files, or intentional examples where they are meaningful. Always verify the changes.
- Be careful when updating the citation policy to not break the examples; ensure the superscript formatting is consistent.

## Verification
- After pushing, the system should reflect the new rules in subsequent LLM prompts.
- Check that the commit appears in the GitHub repository.
- Ensure the swap is active via `swapon --show`.
- Confirm that the citation format in the documentation uses superscript markers like ^[來源簡稱] and that source lists are present.
- Validate that the task router mappings and arbitration rules are correctly updated.

## Sources
- This procedure was derived from a live session where the user requested G3 fix, task router updates, swap configuration, and citation format update to superscript style.
- The Zhiyan AI Legal System documentation files serve as the source of truth.
- See `references/G3_citation_format.md` for a detailed explanation of the G3 rule evolution and the final superscript format.

## Execution Notes

When prioritizing speed over immediate validation (as instructed by user), steps can be executed in this sequence:
1. Ensure swap space (if needed)
2. Fix G3引用格式 (SPACE_CORE) → immediately proceed to
4. Update Task Router (TASK_ROUTER) → then
3. Update Citation Policy (CITATION_POLICY) →
5. Remove temporary citation markers →
6. Verify changes

This allows critical fixes (G3 and task router) to be deployed quickly while deferring citation policy validation for later.

The user explicitly instructed: "依序執行 3 → P2，不必等待 P1 補測。" which maps to:
- Execute G3 fix (their '3')
- Immediately proceed to Task Router review (their 'P2')
- Without waiting for P1補測 (validation of intermediate steps)