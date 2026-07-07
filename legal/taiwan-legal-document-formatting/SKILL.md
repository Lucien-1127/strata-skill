---
name: taiwan-legal-document-formatting
description: Taiwan court/gov/contract document formatting rules.
version: 0.1.0
author: Hermes
platforms: [linux, windows]
tags:
  - Legal
  - Document
  - Formatting
  - Court
  - Contract
  - Government
---

# Taiwan Legal Document Formatting

台灣法律/法務/公司/政府文書排版之完整規則庫，供 Hermes Agent 呼叫執行文件生成、校對與 Word/PDF 重檔任務。

## When to Use

- 生成民事訴訟書狀（起訴狀、答辯狀、聲請狀）
- 生成商業合約（NDA、勞動契約、股東協議書、租賃契約）
- 生成政府公文（令、函、公告、開會通知單）
- Word/PDF 文件跨頁排版修正
- 文件格式轉換與重檔（docx ↔ pdf）

## Prerequisites

- 安裝標楷體/新細明體等法院常用字型（Linux 可裝 `fonts-cwtex-kai`、`fonts-arphic-ukai` 替代）
- fpdf2 / python-docx 用於自動生成
- LibreOffice headless 用於 docx→pdf 轉換（sudo apt-get install -y libreoffice-writer-nogui）

## 規則庫（三軌並行）

### 軌道一：法院書狀（依民事訴訟書狀規則）

| 項目 | 規格 |
|:-----|:------|
| 紙張 | A4，邊界 2.5cm 四邊 |
| 字體 | 標楷體 / 新細明體，14~20 號 |
| 行距 | 單行間距或固定行高 25~30 點 |
| 頁碼 | 頁尾中央阿拉伯數字；超過 30 頁附目錄 |
| 手寫狀限制 | 每頁 18 行，每行 25 字（電腦繕打無此限制） |

### 軌道二：政府公文（依政府文書格式參考規範 105 年版）

| 項目 | 規格 |
|:-----|:------|
| 紙張 | A4，四邊 2.5cm±0.3，左側裝訂線多留 1.5cm±0.3 |
| 字體 | 中文楷書，英數 Times New Roman |
| 字級對應行距 | 10pt→10±3pt / 12pt→20±3pt / 16pt→28±4pt / 20pt→36±5pt |
| 印信位置 | 發文字號與內容間，右側留 7cm±2cm |
| 檔號/保存年限 | 首頁右上，10 點字 |

### 軌道三：商業合約（業界慣例，無強制法規）

| 項目 | 規格 |
|:-----|:------|
| 紙張 | A4，邊界 2~2.5cm |
| 字體 | 微軟正黑體或標楷體 |
| 字級 | 大標 18~20pt / 條款標題 14pt 粗體 / 內文 12pt(或 10.5pt) |
| 行距 | 單行間距或固定行高 20~22pt |
| 防孤行 | 簽章頁必須與至少 1~2 條條文同頁 |
| 騎縫章 | 裝訂側邊界加寬至 2.8cm |

**條款層級縮排規則：**

```
第一條（靠左，粗體）
  項次不冠數字，縮排 2 字
    一、二、三（中文數字，縮排 2 字）
      (一)(二)（縮排 4 字）
        1. 2. 3.（阿拉伯數字，縮排 6 字）
```

**金額寫法：**
大寫中文先行，括號補阿拉伯數字，例如：
`新臺幣伍萬元整（NT$50,000）`

## Word 自動化操作指令

### 段落防斷

段落設定 → 分行與分頁 → 勾選：孤行控制、與下段同頁、段落不分散。

### 表格跨頁

- 選取標題列 → 版面配置 → 重複標題列
- 表格內容 → 列 → 取消勾選「允許列跨頁斷行」防止文字腰斬
- 若需列跨頁但留白過大：檢查文繞圖設為「無」，反覆開關重複標題列重置渲染

### 強制切頁

使用 `Ctrl+Enter` 插入分頁符號，禁用連續 Enter（防止未來編輯跑版）。

### 字距微調（救孤行/孤頁）

字型 → 進階 → 字元間距：加寬/緊密 0.3~0.5 點。

## PDF 重檔技巧

- Word 另存新檔前，先「工具」→「相容性檢查」，避免特殊字元跑位
- 轉存 PDF 時選擇「標準(線上發佈及列印)」品質，勾選「符合 PDF/A」以利長期保存（適用政府/法院文件）
- 若 PDF 頁碼與 Word 顯示不同，需檢查是否有隱藏的分節符號造成頁碼重置
- 掃描簽名頁 PDF 與電腦生成 PDF 合併時，用 Acrobat「合併檔案」而非列印虛擬 PDF，避免解析度不一致

## 判斷邏輯（Agent 決策樹）

1. 若文件遞交對象 = **法院** → 套用軌道一
2. 若文件遞交對象 = **政府機關**（發文/簽呈）→ 套用軌道二
3. 若文件遞交對象 = **民間企業/個人**（合約）→ 套用軌道三
4. 若文件含**長表格** → 額外套用「表格跨頁」規則
5. 若最終輸出為 **PDF** → 額外套用「PDF 重檔技巧」章節

## 本機字型對照（Ubuntu 24.04）

| 法院標準 | 本機替代 | 安裝方式 |
|:---------|:---------|:---------|
| 標楷體（DFKai-SB） | `cwTeXKai` / `AR PL UKai TW` | `fonts-cwtex-kai` / `fonts-arphic-ukai` |
| 新細明體（PMingLiU） | `cwTeXMing` / `AR PL UMing TW` | `fonts-cwtex-ming` / `fonts-arphic-uming` |
| MOICA 自然人憑證 | `moica.nat.gov.tw` | 內政部憑證管理中心，GPKI 架構下第一層下屬憑證機構 |
| 行動自然人憑證 | `fido.moi.gov.tw` | 線上簽署/電子簽章 NDA 用，與 MOICA 不同入口 |
| Times New Roman | Liberation Serif / DejaVu Serif | 內建 |

## 生成管線（Word → PDF）

所有文件統一走：**python-docx → LibreOffice headless → PDF**

### 依賴安裝

```bash
pip3 install python-docx
sudo apt-get install -y fonts-cwtex-kai fonts-cwtex-ming fonts-arphic-ukai fonts-arphic-uming libreoffice-writer-nogui
```

### 一鍵生成腳本

本技能附有 `scripts/generate_doc.py`（載入後用 skill_view 存取），可一鍵選軌道、產 docx、轉 PDF：

```bash
# 法院書狀（cwTeXKai 14pt）
python3 /path/to/scripts/generate_doc.py --track court --title "民事起訴狀" --content 內文.txt --pdf

# 政府公文（AR PL UKai TW 12pt，左裝訂線）
python3 /path/to/scripts/generate_doc.py --track gov --title "開會通知單" --pdf

# 商業合約（Noto Sans CJK TC 12pt，縮排層級）
python3 /path/to/scripts/generate_doc.py --track contract --title "借款契約" --pdf
```

內文格式：每行一段，自動依開頭判斷縮排層級（一、→2字、(一)→4字、1.→6字）。

### 參考文件

- `references/certificates-and-citations.md` — MOICA/fido 網址對照表 + G3 引用格式快速查表 + 簽證基金管理辦法備忘

### 基礎模板

```python
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()

# ── 頁面設定 ──
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)

# ── 字型設定 ──
style = doc.styles['Normal']
font = style.font
font.name = 'cwTeXKai'  # 法院用楷書
font.size = Pt(14)
style.element.rPr.rFonts.set(qn('w:eastAsia'), 'cwTeXKai')

# ── 段落 ──
p = doc.add_paragraph('民事起訴狀')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.runs[0]
run.bold = True
run.font.size = Pt(20)

# ── 內文 ──
p = doc.add_paragraph('事實及理由')
run = p.runs[0]
run.bold = True
run.font.size = Pt(14)

doc.add_paragraph('一、被告於民國115年1月間...')
doc.add_paragraph('（一）雙方簽訂契約約定...')

doc.save('/tmp/output.docx')
```

### LibreOffice 轉 PDF

```bash
libreoffice --headless --convert-to pdf /tmp/output.docx
# 輸出為 /tmp/output.pdf
```

### 三軌道對應參數

| 參數 | 法院書狀 | 政府公文 | 商業合約 |
|:-----|:---------|:---------|:---------|
| 邊距 | 2.5cm | 2.5cm+左1.5cm裝訂 | 2~2.5cm |
| 中文字型 | cwTeXKai | AR PL UKai TW | Noto Sans CJK TC（正黑替代） |
| 英數字型 | Times New Roman | Times New Roman | Times New Roman |
| 內文字級 | 14pt | 12pt | 12pt |
| 標題字級 | 20pt | 16pt | 18pt |
| 行距 | 固定 28pt | 固定 20pt | 固定 22pt |
| 頁碼 | 頁尾中央 | 頁尾中央 | 頁尾中央 |

## 關聯技能

| 技能 | 用途 | 關係 |
|:-----|:-----|:-----|
| `fpdf2-cjk-pdf-generation` | CJK PDF 技術實作（fpdf2 語法、重疊修復） | HOW—將本技能規則轉為 PDF |
| `zhiyan-agent` | 智研法律系統整體設定、TLDS 管線 B | 引用本技能之正式文件規格 |

生成順序：`taiwan-legal-document-formatting`(選軌道) → `fpdf2-cjk-pdf-generation`(產 PDF) → `strat-drill`(審計)

## Pitfalls

- ❌ 法院書狀禁用 `Noto` 系列字型（非標準法院用字）
- ❌ 政府公文日期格式：民國年，如「中華民國 115 年 7 月 7 日」
- ❌ 合約金額寫法不可只用阿拉伯數字
- ❌ 轉 PDF 前未做相容性檢查 → 特殊字元可能跑位
- ❌ 隱藏的分節符號造成頁碼重置 → 轉 PDF 後才發現
- ❌ 表格跨頁斷行未取消 → 文字腰斬無法閱讀
- ❌ 孤行控制未勾選 → 簽章頁獨立在最後一頁
