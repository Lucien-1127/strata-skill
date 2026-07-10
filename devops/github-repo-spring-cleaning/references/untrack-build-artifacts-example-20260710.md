# 實例：清除 `brand-site/` 追蹤（2026-07-10）

## 場景

`zhiyan-mvp` 專案的 Vite build 輸出目錄 `brand-site/`（~21MB, 235 files）被意外
commit。另有 `.bak`、`.thumbnail`、`.pdf` 等工藝品散落在目錄中也被 git 追蹤。

## 步驟

1. **更新 `.gitignore`** — 加入 `brand-site/` + 全域模式
   ```
   brand-site/
   *.bak
   *.thumbnail
   *.pdf
   ```

2. **停止追蹤但保留本機檔案**
   ```bash
   git rm --cached -r brand-site/
   git rm --cached .thumbnail   # 如果 repo root 也有
   ```

3. **檢查還有哪些 `*.bak` 被追蹤（可能在 brand-site/ 之外）**
   ```bash
   git ls-files '*.bak' '*.thumbnail' '*.pdf'
   ```
   本案例中所有 `.bak`/`.pdf` 都在 `brand-site/` 下，已被上一步涵蓋。

4. **Commit 並 push**
   ```bash
   git add .gitignore
   git commit -m "fix: untrack brand-site build artifacts, .bak, .thumbnail, .pdf"
   git push origin main
   ```

5. **驗證**
   ```bash
   git ls-files brand-site/ | wc -l         # 應為 0
   git ls-files ':(*.bak)' | wc -l          # 應為 0
   git ls-files ':(*.thumbnail)' | wc -l    # 應為 0
   git ls-files ':(*.pdf)' | wc -l          # 應為 0
   ```

## 關鍵陷阱

- `git rm --cached` 不會刪除本機檔案 — 檔案在磁碟上完好，只有 git 停止追蹤
- `.gitignore` 只防止**未來**加入 — 已 tracked 的檔案必須先 `git rm --cached`
- 如果 garbage 散落在多個 commit 中（不是僅在 latest commit），需用 `git filter-branch` 改寫歷史（本案例不需要）
