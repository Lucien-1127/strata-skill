---
name: fpdf2-cjk-pdf-generation
description: Generate CJK PDFs with fpdf2 avoiding overlap.
version: 0.3.0
state: inactive
author: Hermes
platforms: [linux]
tags:
  - PDF
  - fpdf2
  - CJK
  - Layout
  - Noto-Font
  - G3-Citation
---

# fpdf2 CJK PDF 排版指南（已棄用）

> **⚠️ 注意：自 2026-07-07 起，所有文件改走 Word 管線（python-docx → LibreOffice → PDF）。**
> 本技能保留僅供參考歷史失敗模式，新文件請載入 `taiwan-legal-document-formatting`（選軌道）後走 Word 管線。

## 棄用原因

fpdf2 直接產 PDF（管線A）有以下先天限制：
- CJK 文字渲染座標計算與拉丁字元不同，反覆出現重疊/溢排（v1~v5 迭代證實無法根治）
- 無法使用法院標準字型（標楷體、新細明體等非向量字型）
- 無法產出 .docx 中間檔供人工校對
- 超過 30 頁無法自動產生目錄

## 替代方案

改用 **python-docx → LibreOffice headless → PDF** 管線：
1. `taiwan-legal-document-formatting` — 選軌道（法院/政府/合約）
2. python-docx — 套用軌道規則產出 .docx
3. LibreOffice — 轉 PDF

## When to Use

**不使用。** 新文件一律走 Word 管線。

## When to Use

- 用戶要求產出 PDF（知識文件、分析報告、研究報告）
- 需要自動生成中文 PDF 文件
- 遇到 fpdf2 CJK 文字重疊 / 溢排問題

## Prerequisites

```bash
pip3 install fpdf2
sudo apt-get install -y fonts-noto-cjk
sudo apt-get install -y poppler-utils    # 用於 pdftoppm 排版驗證
```

字型路徑：
```
# 管線 A — 知識文件（fpdf2 直出）
Noto Serif CJK TC Regular → /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc
Noto Serif CJK TC Bold    → /usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc
Noto Sans CJK TC Regular  → /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc

# 管線 B — 正式書狀（DOCX→LibreOffice→PDF）
cwTeXKai (楷書, 標楷體替代)  → /usr/share/fonts/truetype/cwtex/cwTeXKai.ttf
cwTeXMing (明體, 新細明體替代) → /usr/share/fonts/truetype/cwtex/cwTeXMing.ttf
AR PL UKai TW (楷體)          → /usr/share/fonts/truetype/arphic/ukai.ttc
AR PL UMing TW (明體)          → /usr/share/fonts/truetype/arphic/uming.ttc

# 補充字型
Noto Serif CJK TC 現有 7 級字重 (ExtraLight~Black) 同一 ttc 檔
WenQuanYi Micro Hei → /usr/share/fonts/truetype/wqy/wqy-microhei.ttc
BabelStone Han       → apt install fonts-babelstone-han
```

## How to Run

`terminal(command="python3 /path/to/gen_pdf.py", timeout=30)`

## Procedure

### 0. 核心排版常數

```python
MARGIN_L = 20           # 左/右邊界 (mm)
INDENT = 34             # 內文縮排
LH = 5.8                # CJK 行高 (9.5pt 字型)
A4_H = 297
BOTTOM = 18             # 底部自動換頁邊界
```

### 1. 子項目排版（核心模式 — 唯一可靠方式）

**兩行 multi_cell 分開寫**：label 獨立一行，body 下一行縮排。不同 Y 位置，絕對零重疊。

```python
def item(label, body):
    """子項目：label 一行 + body 一行，零重疊"""
    need(35)
    pdf.set_x(INDENT)
    pdf.set_font('NotoSerif', 'B', 9.5)
    pdf.set_text_color(20, 40, 85)
    pdf.multi_cell(0, LH, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(INDENT + 4)
    pdf.set_font('NotoSerif', '', 9.5)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, LH, body, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)
```

**失敗方法（已實證不可行）：**
- ❌ `cell(W)` + `multi_cell(0)` — cell 中 CJK 字元溢排至相鄰區域
- ❌ `cell(W)` + `multi_cell(W_fixed)` — 同Y同排但CJK溢排cell邊界仍重疊
- ❌ `write()` — CJK line break 以拉丁字母為準，中文溢排
- ✅ **唯一解法**：不同Y位置（label一行、body下一行），X永遠不交錯

### 2. 章節標題

```python
def heading(num, title):
    need(18)
    pdf.set_fill_color(20, 40, 85)    # 藏青底
    pdf.set_text_color(255, 255, 255)  # 白字
    pdf.set_font('NotoSerif', 'B', 9)
    pdf.cell(8, 7, num, fill=True, align='C')
    pdf.set_text_color(20, 40, 85)
    pdf.set_font('NotoSerif', 'B', 12)
    pdf.cell(4)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
```

### 3. 摘要框（淺藍背景 + 藏青邊框）

```python
bx, by, bw = 18, pdf.get_y(), 174
pdf.set_fill_color(240, 246, 255)
pdf.set_draw_color(20, 40, 85)
pdf.set_line_width(0.4)
pdf.set_xy(bx + 4, by + 2)
pdf.set_font('NotoSerif', 'B', 10)
pdf.set_text_color(20, 40, 85)
pdf.cell(0, 7, '摘  要')
pdf.set_xy(bx + 4, pdf.get_y() + 1)
pdf.set_font('NotoSerif', '', 9.5)
pdf.set_text_color(55, 55, 55)
pdf.multi_cell(bw - 8, LH, summary_text)
ey = pdf.get_y()
pdf.rect(bx, by, bw, ey - by + 4)
pdf.set_y(ey + 6)
```

### 4. 法條引用框（淺灰背景 + 藍灰邊框）

```python
def law_box(text, title):
    need(45)
    bx = INDENT; by = pdf.get_y()
    pdf.set_xy(bx+3, by+2)
    pdf.set_font('NotoSerif', 'B', 8.5)
    pdf.set_text_color(20, 40, 85)
    pdf.multi_cell(152, 4.5, title, new_x="LMARGIN", new_y="NEXT")
    tl_end = pdf.get_y()
    pdf.set_xy(bx+3, tl_end + 0.5)
    pdf.set_font('NotoSerif', '', 8.5)
    pdf.set_text_color(55, 55, 70)
    pdf.multi_cell(152, 4.5, text, new_x="LMARGIN", new_y="NEXT")
    ey = pdf.get_y() + 3
    pdf.set_fill_color(245, 245, 250)
    pdf.set_draw_color(130, 150, 180)
    pdf.set_line_width(0.3)
    pdf.rect(bx, by, 158, ey - by)
    pdf.set_y(ey + 1)
```

### 5. 表格

```python
def tbl(headers, rows, col_w):
    pdf.set_x(MARGIN_L)
    pdf.set_fill_color(20, 40, 85)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('NotoSerif', 'B', 9)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align='C')
    pdf.ln()
    pdf.set_font('NotoSerif', '', 8.5)
    for i, row in enumerate(rows):
        pdf.set_x(MARGIN_L)
        bg = (245, 248, 252) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(60, 60, 60)
        pdf.set_font('NotoSerif', 'B', 8.5)
        pdf.cell(col_w[0], 7, row[0], border=1, fill=True)
        pdf.set_font('NotoSerif', '', 8.5)
        for j in range(1, len(row)):
            pdf.cell(col_w[j], 7, row[j], border=1, fill=True,
                     align='C' if j == 1 else 'L')
        pdf.ln()
```

### 6. 頁面保護與末頁填充

```python
A4_H, BOTTOM = 297, 18

def need(mm=25):
    if A4_H - BOTTOM - pdf.get_y() < mm:
        pdf.add_page()

rem = A4_H - BOTTOM - pdf.get_y()
if pdf.page_no() >= 2 and rem < 130:
    pdf.ln(130 - rem)
```

### 7. 完整標準模板

```python
from fpdf import FPDF
from datetime import date

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('NotoSerif', '', 7.5)
            self.set_text_color(140, 140, 140)
            self.cell(0, 6, '頭標', align='L'); self.ln(10)
    def footer(self):
        self.set_y(-14)
        self.set_font('NotoSerif', '', 7.5)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f'— 第{self.page_no()}頁 —', align='C')

pdf = PDF('P', 'mm', 'A4')
pdf.add_font('NotoSerif', '', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
pdf.add_font('NotoSerif', 'B', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc')
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_margin(20)
```

### 8. G3 引用格式區塊（法律 PDF 專用）

文中 `^[來源簡稱]`，章末 `【本段資料來源】`。

```python
def src_block(sources):
    need(15)
    pdf.set_x(INDENT)
    pdf.set_font('NotoSerif', 'B', 8)
    pdf.set_text_color(180, 140, 60)
    pdf.cell(0, 4.5, '【本段資料來源】', new_x="LMARGIN", new_y="NEXT")
    for s in sources:
        pdf.set_x(INDENT + 4)
        pdf.set_font('NotoSerif', '', 8)
        pdf.set_text_color(180, 140, 60)
        pdf.cell(0, 4, f'  ^{s}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)
```

### 9. 自動排版驗證（腳本末段嵌入）

```python
subprocess.run(['pdftoppm','-png','-r','200',out_pdf,'/tmp/_vfy'],capture_output=True)
from PIL import Image; import numpy as np
for p in range(1, pdf.page_no()+1):
    img = Image.open(f'/tmp/_vfy-{p}.png')
    arr = np.array(img.convert('L'))
    overlap = sum(1 for y in range(0,arr.shape[0],2)
        if 0.55 < (arr[y,20:arr.shape[1]-20]<80).mean() <= 0.85)
    print(f'  p{p}: {"✅" if overlap<=5 else "❌"}')
print(f'  Total: {pdf.page_no()}p')
```

### 10. 產出前檢查點（自動閘門系統）

PDF 產出後，自動通過以下 3 道檢查點後才送模型委員會審計：

#### 檢查點 A：軌道合規檢查

比對輸出是否符合所選軌道的邊距、字型規格。

| 軌道 | 邊距 | 字型 | 最小字級 |
|:-----|:----:|:-----|:--------:|
| 法院書狀 | 25mm | cwTeXKai / AR PL UKai TW | 14pt |
| 政府公文 | 25mm + 左15mm裝訂 | AR PL UKai TW | 10pt |
| 商業合約 | 20mm | Noto Sans CJK TC | 12pt |

```python
def check_track(track, pdf):
    spec = {'court':25, 'gov':25, 'contract':20}
    if pdf.l_margin != spec[track]:
        return f'❌ 邊距不符: {pdf.l_margin}≠{spec[track]}mm'
    return '✅'
```

#### 檢查點 B：引用完整性檢查

確認所有 `^[來源]` 都有對應的來源條目。

```python
def check_cites(text):
    import re
    cites = set(re.findall(r'\^\[([^\]]+)\]', text))
    sources = set()
    for m in re.finditer(r'【本段資料來源】\n((?:\^.*\n?)*)', text):
        for s in re.findall(r'\^([^\n]+)', m.group(1)):
            sources.add(s.strip())
    missing = [c for c in cites if c.split()[0] not in ' '.join(sources) and ' ' not in c]
    if missing: return f'❌ 孤立引用: {missing}'
    return '✅'
```

#### 檢查點 C：燈號強制閘門

Drill 報告必須為 🟢 綠燈才交付。

```python
def gate(report):
    if '🟢' in report[:100]: return '✅ PASS'
    if '🔴' in report: return '🔴 BLOCKED'
    return '⚠️ 無燈號'
```

#### 完整流程

```
選軌道 → 產PDF → A合規 → B引用 → Drill → C閘門 → 交付
                   ❌退回   ❌退回    🔴退回   🟢通過
```

## Pitfalls

- ❌ **`cell()` + `multi_cell()` 同排** — CJK 字元溢排。**永遠用 multi_cell 分兩行**。
- ❌ **`write()` 處理 CJK** — 中文 line break 以拉丁字母為準，會溢排。
- ❌ **Emoji 字元** — Noto Serif CJK 無 emoji，改用文字標記。
- ❌ **行高 5.5mm 以下** — CJK 需要足夠行高，建議 5.5~6.0mm。
- ❌ **硬編碼法條框高度** — 用 multi_cell 動態計算。
- ❌ **子項目跨頁** — 每個 `item()` 前 `need(35)`。
- ❌ **末頁留白** — 自動補附錄或留白。
- ❌ **文件類別混用** — 知識文件用 fpdf2，正式文件走 TLDS 管線。
- ❌ **不附來源** — 法律條文附 `^[來源]` 與章末列表。
- ❌ **跳過 STRATA 管線** — 法律 PDF 必須經模型委員會審計。
- ❌ **MOICA 網址 typo** — `moea`(經濟部) vs `moica`(內政部)，差一個字母。
- ❌ **證交法 §20/§171 刑度混淆** — §20 無刑罰，違反者歸 §171。
- ❌ **學說見解掛法條引用** — 學說歸學說，法條歸法條，來源層級不可混。

## Verification

```bash
# 快速驗證 PDF
file /path/to/output.pdf
python3 -c "import re; c=open('/path/to/output.pdf','rb').read(); print(len(re.findall(b'/Type\s*/Page[^s]',c)),'頁')"

# 像素驗證
pdftoppm -png -r 200 output.pdf /tmp/vfy
python3 -c "
from PIL import Image; import numpy as np
for p in range(1, 6):
    img = Image.open(f'/tmp/vfy-{p}.png')
    arr = np.array(img.convert('L')); ov = 0
    for y in range(0, arr.shape[0], 2):
        d = (arr[y,20:arr.shape[1]-20] < 80).mean()
        if 0.55 < d <= 0.85: ov += 1
    print(f'p{p}: {\"✅\" if ov<=5 else \"❌\"} ov={ov}')
"

# 引用格式驗證
skill_view(name="fpdf2-cjk-pdf-generation", file_path="references/citation-verification-checklist.md")
```

## References

- `references/citation-verification-checklist.md` — G3 引用格式驗證檢查表（模型委員會審計標準）
- `references/v1-v6-failure-modes.md` — 六次迭代失敗模式記錄（換模型/字型前先查）

## 關聯技能

| 技能 | 用途 | 關係 |
|:-----|:-----|:-----|
| `taiwan-legal-document-formatting` | 三軌排版規則（法院/政府/合約） | WHAT—定義規格，本技能實作 |
| `strat-drill` | 模型委員會審計 | 產出後強制走審計流程 |
