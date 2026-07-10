# 法律知識 PDF 文件生成指南

> ⚠️ **fpdf2 管線（管線 A）已棄用。** 所有文件統一走 Word 管線：python-docx(w/防孤行) → LibreOffice → PDF → bash驗證 → QA雙子代理 → 交付。
>
> 詳細 SOP 請載入 `taiwan-legal-document-formatting` 技能。
> 以下 fpdf2 內容保留僅供參考歷史失敗模式，不應用於新文件。
>
> **排版確認日期：2026-07-07** — 對齊 TLDS v1.0.0 字體規範。新增 CJK 行高與多行重疊陷阱。
> 字型使用 Noto Serif CJK TC（建議字型），而非 wqy-zenhei。

## 概述

兩條管線（**管線 A 已棄用**）：

| 管線 | 適用場景 | 技術棧 | 狀態 |
|:-----|:---------|:-------|:----:|
| **A — 知識文件（快速）** | 法律知識說明、摘要、分析報告 | fpdf2 直出 PDF | ❌ 已棄用 |
| **B — 正式文件（TLDS）** | 契約、登記文件、法院書狀 | python-docx → LibreOffice headless → PDF | ✅ 現行管線 |

## 環境準備

### 依賴
```bash
pip3 install fpdf2 python-docx
sudo apt-get install -y fonts-noto-cjk libreoffice-writer-nogui
```

### 字型路徑（TLDS 建議字型）
```
Noto Serif CJK TC Regular → /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc
Noto Serif CJK TC Bold    → /usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc
Noto Sans CJK TC Regular  → /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
```

> ⚠️ fpdf2 中 TTC 字型可直接使用。font name 用 `'Noto Serif CJK TC'` 或 `'Noto Sans CJK TC'`。

## 管線 A：知識文件（fpdf2 直出）

### 全域參數
```python
pdf = FPDF('P', 'mm', 'A4')
pdf.add_font('NotoSerif', '', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
pdf.add_font('NotoSerif', 'B', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc')
pdf.add_font('NotoSans', '', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
pdf.set_auto_page_break(auto=True, margin=22)
pdf.set_margin(20)
```

### Header（僅第 2 頁起顯示）
```python
def header(self):
    if self.page_no() > 1:
        self.set_font('NotoSerif', '', 7.5)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, '智研法律 AI 系統  •  {文件標題}', align='L')
        self.ln(10)
```

### Footer（全頁）
```python
def footer(self):
    self.set_y(-15)
    self.set_font('NotoSerif', '', 7.5)
    self.set_text_color(160, 160, 160)
    self.cell(0, 10, f'— 第 {self.page_no()} 頁 —', align='C')
```

## 文件結構慣例（知識文件）

| 頁面 | 內容 | 字型 |
|:-----|:-----|:-----|
| p1 **封面** | ln(55) 留白 → 26pt 粗體主標 → 0.6pt 分隔線 → 11pt 副標 → 9pt 日期+系統名 | 26B / 11 / 9 |
| p2 **主文** | 摘要框（淺藍底 #F0F6FF + 藏青邊框）→ 編號章節（藍底白字標號 + 12pt 標題）→ 細灰分割線 | 9.5 內文 |
| p3+ **分析** | 15pt 大標 + 底線 → 11.5pt 次標 → 結構式子項（粗體標籤+灰說明）→ 細灰底線 | 15B / 11.5B / 9.5 |
| 末頁 **免責** | 細線分隔 → 8pt 灰字聲明（「不構成法律意見」） | 8 |

## 配色方案（使用者確認 ✅）

| 用途 | RGB | 色名 |
|:-----|:---:|:-----|
| 主標題 / 主題色 | `(20, 40, 85)` | 深藏青 #142855 |
| 內文 | `(60, 60, 60)` | 深灰 |
| 摘要背景 | `(240, 246, 255)` | 淺藍 #F0F6FF |
| 摘要邊框 | `(20, 40, 85)` | 同主題色 |
| 分割線 | `(215, 215, 215)` | 淺灰 |
| 頁首頁尾 | `(140, 140, 140)` / `(160, 160, 160)` | 中灰 |
| 免責宣告 | `(140, 140, 140)` | 中灰 8pt |

## 標準版面元素（管線 A — fpdf2 直出）

### ⭐ 核心排版原則 (2026-07-07)

**CJK 文字用 `write()` 流式排版，不用 `cell()` + `multi_cell(0)`。**

原因是 `multi_cell(0, ..., new_x="LMARGIN")` 第二行起會將 x 重設至左邊界，與前面元素在 Y 軸重疊。
`write()` 像 Word 排版引擎，標籤與內文自然流在同一行，遇右邊界自動換行，字型切換可 mid-stream，零重疊風險。

### 1. 封面（p1）
```python
pdf.add_page()
pdf.ln(55)
pdf.set_font('NotoSerif', 'B', 26)
pdf.set_text_color(20, 40, 85)
pdf.multi_cell(0, 14, '文件主標題', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)
pdf.set_draw_color(20, 40, 85)
pdf.set_line_width(0.6)
pdf.line(65, pdf.get_y(), 145, pdf.get_y())
pdf.ln(10)
pdf.set_font('NotoSerif', '', 11)
pdf.set_text_color(90, 90, 90)
pdf.multi_cell(0, 7, '副標題', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(40)
pdf.set_font('NotoSerif', '', 9)
pdf.set_text_color(130, 130, 130)
pdf.cell(0, 6, today_str, align='C', new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, '智研法律 AI 系統', align='C', new_x="LMARGIN", new_y="NEXT")
```

### 2. 摘要框
```python
pdf.set_fill_color(240, 246, 255)
pdf.set_draw_color(20, 40, 85)
pdf.set_line_width(0.4)
bx, by, bw = 18, pdf.get_y(), 174
pdf.set_xy(bx + 4, by + 2)
pdf.set_font('NotoSerif', 'B', 10)
pdf.set_text_color(20, 40, 85)
pdf.cell(0, 7, '摘  要')
pdf.set_xy(bx + 4, pdf.get_y() + 1)
pdf.set_font('NotoSerif', '', 9.5)
pdf.set_text_color(55, 55, 55)
pdf.multi_cell(bw - 8, 6, '摘要文字...')
by2 = pdf.get_y()
pdf.rect(bx, by, bw, by2 - by + 4)
pdf.set_y(by2 + 8)
```
### 3. 編號章節 + 子項目（write() 流式排版 — 推薦）

2026-07-07 實戰發現：CJK 字型下 `cell()` + `multi_cell(0)` 在同 Y 軸起跑會導致文字重疊。
**推薦使用 `write()` 流式排版**：

```python
y0 = pdf.get_y()
pdf.set_x(INDENT)
pdf.set_font('NotoSerif', 'B', 9.5)
pdf.set_text_color(*NAVY)
pdf.write(LINE_H, label + '  ')          # 標籤
pdf.set_font('NotoSerif', '', 9.5)
pdf.set_text_color(*DARK)
pdf.write(LINE_H, body)                   # 內文自然接在標籤後
# 若未自動換行則強制換行
if pdf.get_y() == y0:
    pdf.ln(LINE_H)
pdf.ln(GAP)
```

`write()` 像 Word 一樣自然流排：標籤和內文在同行、遇到右邊界自動換行、
換行後從左邊界繼續。字型切換可以 mid-stream 進行，不可靠的 `new_x`/`new_y` 行為不再影響排版。

### 4. 編號章節 + 子項目（multi_cell 兩行法 — 備用）

```python
pdf.set_fill_color(20, 40, 85)
pdf.set_text_color(255, 255, 255)
pdf.set_font('NotoSerif', 'B', 9)
pdf.cell(8, 7, str(num), fill=True, align='C')
pdf.set_text_color(20, 40, 85)
pdf.set_font('NotoSerif', 'B', 12)
pdf.cell(4)
pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_x(32)
pdf.set_font('NotoSerif', '', 9.5)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(0, 6, desc, new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)
for label, text in bullets:
    # 標籤與內文分兩行：避免 CJK 文字在 same-y 重疊
    pdf.set_x(36)
    pdf.set_font('NotoSerif', 'B', 9.5)
    pdf.set_text_color(20, 40, 85)
    pdf.multi_cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(40)
    pdf.set_font('NotoSerif', '', 9.5)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
pdf.set_draw_color(215, 215, 215)
pdf.set_line_width(0.2)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(4)
```

### 5. 免責聲明
```python
pdf.ln(6)
pdf.set_draw_color(180, 180, 180)
pdf.set_line_width(0.3)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(3)
pdf.set_font('NotoSerif', '', 8)
pdf.set_text_color(140, 140, 140)
pdf.multi_cell(0, 4.5, 
'免責聲明：本文由智研法律 AI 系統生成，僅供法律知識參考，不構成具體法律意見。如有個案需求，請諮詢合格律師。')
```

## 管線 B：正式文件（TLDS 規範）

正式文件生成請參照：
- **`/home/ysga1/zhiyan-legal/docs/80_技術參考/TLDS-v1.0.0.md`** — 完整版面規格
- **核心**：Part B（版面規格）、Part D（字體規則）、Part N（輸出管線）

TLDS 核心差異：
- 邊距：T/B 25mm, L 30mm（含裝訂區）, R 25mm
- 字級：標題 18pt / H1 14pt / 內文 12pt，固定行距 24pt
- 字型：Noto Serif TC（內文）/ Noto Sans TC（表格）
- 管線：DOCX (python-docx, 套用 §B.3 Style) → LibreOffice headless → PDF (subset embedding)
- 品質：FEG_TLDS 7 維度評分（A-G）
- 頁碼：「第 X 頁，共 Y 頁」置中

## 流程

> ⚠️ **以下流程已由 `taiwan-legal-document-formatting` 技能的 8 步驟 SOP 取代。**
> 新流程：選軌道 → python-docx(w/防孤行) → LibreOffice → bash驗證 → QA雙子代理 → ✅交付/❌修正
>
> 舊管線 A/B 選擇流程保留僅供參考。

1. 判斷文件類型 → 選擇管線 A（知識文件）或 B（正式文件/TLDS）
2. 解析內容結構 → 提取標題、摘要、章節、子項
3. 生成腳本 → 執行 → 驗證頁數/大小
4. 交付：`MEDIA:/path/to/output.pdf`

## 陷阱

- **`fpdf2` 的 `uni=True` 已棄用**（v2.5.1+）— 直接省略
- **`new_x="LMARGIN", new_y="NEXT"`** — fpdf2 2026+ 需要這兩個參數控制游標
- **分隔線**：`line()` 不移動游標，需手動 `ln()`
- **摘要框**：`rect()` 不移動游標，需 `set_y()` 跳到框後
- **免責聲明**：每份文件必含，且必須有「不構成法律意見」警語
- **TLDS 字體規則 D-1**：伺服器端僅允許 Noto 系列，禁止 DFKai-SB / PMingLiU
- **TLDS 規則 D-3**：PDF 必須嵌入字體 (subset embedding)
- **正式文件**：**不可直接 fpdf2 生成**，須走 DOCX→LibreOffice 管線
- **🚨 CJK `cell()` + `multi_cell()` 同 Y 軸重疊**（2026-07-07 實戰發現）：
  ```python
  # ❌ 錯誤：cell() 畫完標籤後 multi_cell() 從同 Y 起跑，內文第一行與標籤重疊
  pdf.cell(30, 5.5, label)       # 游標右移
  pdf.multi_cell(0, 5.5, body)   # multi_cell 重置 x 到左邊界，但 Y 不變
  # → body 第一行與 label 在 x=36~81 重疊
  ```
  **解法**：標籤與內文分兩行，各自用 `multi_cell()`：
  ```python
  # ✅ 正確：兩行 multi_cell，游標自然換行
  pdf.multi_cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
  pdf.set_x(40)
  pdf.multi_cell(0, 6, body, new_x="LMARGIN", new_y="NEXT")
  ```
- **🚨 CJK 行高不足**：CJK 字形在 9.5pt 時建議 `6.0mm` 行高（`5.5mm` 會讓中文字幾乎貼在一起）
- **🚨 Noto Serif CJK 不含 Emoji**：emoji 會跳 missing glyphs 警告，需改用字體回退或移除

## 法律分析 PDF 的特殊要求（使用者明確指示）

### 中立立場
- 不預設違法故意。用「可能涉及」「宜注意」「相關法條框架」取代「構成犯罪」「違反」「違法」
- 保留「應由司法機關依具體事實判斷」等客觀敘述
- 區分「條文框架」與「個案事實」，不代人下結論

### 引用格式
- 全文嵌入式引用：在敘述後加 `(全國法規資料庫)` `(內政部)` `(相關判決)` 等
- 避免只集中在文末參考資料區
- 法條引文框（law_box）內附註來源

### 排版輔助函數一覽（可複製 `scripts/legal-analysis-pdf-template.py`）

| 函數 | 用途 | 防護 |
|:-----|:-----|:------|
| `check_space(mm)` | 檢查剩餘空間，不足換頁 | 跨頁斷層 |
| `section(num, title)` | 編號章節標題 | check_space(18) |
| `sub_item(label, body)` | 標籤+內文（兩行 multi_cell） | check_space(30) + 防重疊 |
| `body_text(text)` | 純內文 | check_space(10) |
| `bold_text(text, color)` | 粗體結論 | check_space(10) |
| `divider()` | 淺灰分隔線 | check_space(8) |
| `law_box(...)` | 法條引文框（動態高度） | check_space(45) |
| `table(headers, rows, col_w)` | 通用表格 | — |
| 末頁填補 | `if final < 130: pdf.ln(...)` | 最後一頁太空 |