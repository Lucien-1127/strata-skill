---
name: creative-production
description: Use when 用自己的寫手寫作、續篇改稿或製作劇本分鏡.
version: 0.1.0
author: Lucien, Hermes Agent
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [寫作, 劇本, 分鏡, 素材一致性, 自用]
    related_skills: [writer-compiler, hypit]
---

# 我的創作製作流程

把已確認的方向落成正文、劇本和可交接的分鏡資產包。這是自己的製作規範，不是 BookFlow 或 manju 的換名整包安裝。可聯網查證與使用生成服務；先做不收費的本機契約檢查，再按授權進入實際製作。

## When to Use

- 直接寫文章、小說、系列正文、續篇、局部改稿，或使用已編譯寫手。
- 把故事改成短劇／漫劇、劇本、角色場景資產清單與分鏡提示詞。
- 接續中斷的創作專案、校對前後設定、準備影片生成交接。
- 只要編譯系統指令，用 `writer-compiler`；單次一般問答不建立製作專案。

## 前置盤點

1. 從使用者已有素材、專案位置及最新進度找起；讀 Brief、版本與未完成項，不因新會話重新立項。
2. 分清 `narrative`（敘事）及 `nonfiction`（非敘事）。再分 `writing`（正文）及 `screen`（影片前期）。不確定會實質改變內容時才問。
3. 保留已確認受眾、風格與字數。沒有寫手指令也可直接寫，不強制先走編譯器；缺少必要系列設定則先提出短規劃確認。
4. 選最小交付：單篇不強制做 JSON 專案；系列、多次改稿或影片交接必須保存專案檔。採 `references/project-contract.md` 與模板。

## 製作流程

### 正文執行

必讀 `references/writing-execution.md`。順序為：brief → 大綱 →（僅敘事需要時）角色 → 正文 → 編修 → 人工定稿 → 發布準備 → 真實資料復盤。

按使用者目標與題材選擇節奏，不強制每段衝突、每章鉤子、禁用人名或固定三幕比例。先寫好內容，再用適量檢查發現問題；評分不是測得的點擊率或收益。

### 影片前期

必讀 `references/screen-preproduction.md`。順序為：劇本定稿 → 實體／聲音清單 → 所需資產確認 → 分鏡 → 生成交接。

把故事事實、視覺外觀及實際時間分別交給核准劇本、核准資產、量測音訊負責。不把「唯一真相」寫成互相覆蓋的規則。

### 本機檢查與實際生成

用 `terminal` 執行技能目錄內：

```text
python3 scripts/validate_project.py /absolute/project/project.json
```

請先從 `skill_view` 回傳取得技能絕對路徑，或將 `workdir` 設為該技能目錄；不要在任意 cwd 猜相對位置。

- 檢查器只讀取專案內檔案，exit 0 表示本版契約檢查通過，exit 1 表示阻擋。`executed:false` 永遠代表未執行生成。
- 它檢查版本、字數、引用、資產狀態、路徑與時長來源；不證明故事好看、圖片內容正確或使用者真的核准。
- `generation.requested:false` 是「這份檔案只做前期檢查」，不是禁止整個專案聯網。不要改成 true 企圖觸發生成；它沒有生成 API。
- 使用者要生成時，先完成檢查，另確認供應商、帳號、費用或預算及工作範圍，交給既有製作引擎。詳細邊界見 `references/engine-handoff.md`。

## 修改與復驗

每次修改保存新版本與最小影響範圍。先查局部，再查依賴（角色／資產／分鏡／時長），最後查整體。舊素材仍有用就保留，不因一次失敗重跑所有付費工作。不能對所有變更一律改全稿。

## 交付標準

- 回覆結論與可用檔案，正文和 QA／專案紀錄分開；不將內部製作表當成文稿。
- 不將草稿、待確認素材、前期檢查通過、生成成功、審片完成混為一談。
- 最終影片要實際觀看及聆聽；本技能的本機測試不等於審片或實際 API 驗證。
- 不自動公開發布、不自動購買、不保存憑證至專案。對生成已有明確預算授權時沿用範圍，超出才重問。
- 使用說明與研究筆記預設存 Obsidian 收件匣；程式、素材、JSON 與測試留在專案，避免把 vault 當建置目錄。

## Verification

透過 `terminal` 在技能目錄執行 `python3 -m unittest discover -s scripts/tests -v`。

範例是明示的原創測試稿，不代表使用者已核准真實作品。用 `templates/writing-project.json` 搭配 `templates/draft.md` 可檢查正文；`templates/screen-project.json` 是無角色的一鏡前期樣本。

## Pitfalls

不要照搬上游 HTML 看板、規避平台審查的用詞技巧、未證實的流量與模型限制。新增腳本必須先寫失敗測試再實作；未引用素材或未知能力寧可阻擋。參考及授權見 `references/provenance.md`。
