# Inline Underline Fields with fpdf2

For **simple contract/forms** where the deprecated fpdf2 pipeline is still useful (quick form generation with fillable fields). The Word pipeline is preferred for multi-page formal documents, but fpdf2 + inline underlines works well for one-off contract templates ≤5 pages.

## Core Technique

Use `pdf.write()` for flowing inline text segments combined with `pdf.line()` drawn at the cursor position for each field. The cursor advances past the underline so the next text segment flows naturally.

```python
# Inline render helper
def inline(self, *segments):
    """Segments: ('t', str) for text, ('f', width_mm) for underlined field."""
    self.set_font('Kai', '', 12)
    for typ, data in segments:
        if typ == 't':
            self.write(LINE_H, data)
        elif typ == 'f':
            w = data  # mm
            x = self.get_x()
            y = self.get_y()
            # Page-right-edge guard
            if x + w > LEFT_MARGIN + CONTENT_W - 2:
                self.ln(LINE_H)
                x, y = self.get_x(), self.get_y()
            # Draw underline slightly below text baseline
            self.set_line_width(0.4)
            self.line(x + 0.5, y + LINE_H - 1.5,
                      x + w - 0.5, y + LINE_H - 1.5)
            self.set_x(x + w)
    self.ln(LINE_H)
```

## Table Row with Underline Fields (Data Entry Tables)

For tables where header columns are labeled and data cells are blank underlined fields (e.g., property registration tables in contracts):

```python
def table_row(pdf, label, col_widths, field_widths, line_h=7):
    """Render a table row: label cell + N underlined data cells."""
    pdf.set_font('Kai', '', 10)
    x0 = pdf.get_x()
    # First column is the row label (e.g. '土地' or '建物')
    pdf.cell(col_widths[0], line_h, label, border=0)
    # Remaining columns: draw underlines
    for i, fw in enumerate(field_widths):
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.cell(fw, line_h, '', border=0)
        pdf.set_line_width(0.35)
        pdf.line(x + 1, y + line_h - 1.5, x + fw - 1, y + line_h - 1.5)
    pdf.ln(line_h)
```

Usage:
```python
# Table header
headers = ['標的物類型', '鄉鎮市區', '段／小段．門牌', '地號／建號', '權利範圍']
col_w = [28, 30, 44, 34, 30]
for i, h in enumerate(headers):
    pdf.cell(col_w[i], 6, h, align='C')
pdf.ln(7)
# Data rows with underlines
table_row(pdf, '土地', col_w, [col_w[1], col_w[2], col_w[3], col_w[4]])
table_row(pdf, '建物', col_w, [col_w[1], col_w[2], col_w[3], col_w[4]])
```

## Centered Date Line with Underlines

For date fields centered at the bottom of a signature page (e.g. "中華民國 年 月 日"):

```python
pdf.set_font('Kai', '', 12)
pdf.cell(CONTENT_W, 10, '中  華  民  國     年     月     日',
         new_x='LMARGIN', new_y='NEXT', align='C')

# Draw underlines for each date field beneath the centered text
cx = LEFT_MARGIN + CONTENT_W / 2  # center X
y = pdf.get_y() - 8               # back up to the text line
pdf.set_line_width(0.35)
pdf.line(cx - 38, y + 7, cx - 18, y + 7)  # 民國
pdf.line(cx - 8,  y + 7, cx + 12, y + 7)  # 年
pdf.line(cx + 5,  y + 7, cx + 25, y + 7)  # 月
pdf.line(cx + 22, y + 7, cx + 38, y + 7)  # 日
```

## Positioning Math

| Parameter | Value | Note |
|-----------|-------|------|
| LINE_H (12pt) | 7 mm | Standard line height for 12pt CJK |
| Underline Y offset | `y + LINE_H - 1.5` | ~1.5mm above next line's baseline |
| Line width | 0.35–0.4 mm | Visible but not heavy |
| Field edge gap | 0.5 mm | Small inset so lines don't touch adjacent text |
| Right-margin threshold | CONTENT_W - 2 | 2mm buffer before line-break |
| Table underline Y offset | `y + line_h - 1.5` | Same formula, different row height |

## Font Glyph Issues

| Missing Glyph | Font | Fix |
|---------------|------|-----|
| `・` (U+30FB, katakana middle dot) | cwTeXKai | Replace with `．` (U+FF0E, full-width dot) |
| `✓` or checkmarks | cwTeXKai/UMing | Replace with `v` or `○` |
| Any emoji | CJK fonts | Use text markers instead |

## Table with Underline Fields

For tables with blank fields in data columns:

```python
col_widths = [28, 30, 44, 34, 30]
pdf.table_row = lambda label, cw, fw: (
    pdf.cell(cw[0], 7, label, border=0),
    [pdf.line(pdf.get_x()+1, pdf.get_y()+5.5,
              pdf.get_x()+fw[i]-1, pdf.get_y()+5.5)
     or pdf.cell(fw[i], 7, '', border=0) for i in range(len(fw))],
    pdf.ln(7)
)
```

## When to Use vs. Word Pipeline

| Criteria | fpdf2 + Underlines | Word Pipeline |
|----------|-------------------|---------------|
| Pages | ≤5 | Any |
| Underline fields | ✅ Native | Must use table borders |
| CJK rendering | ⚠️ Manual | ✅ Native |
| .docx editing | ❌ | ✅ |
| Court standard fonts | ⚠️ (cwTeXKai ≈ 標楷體) | ✅ |
| Quick one-off forms | ✅ | ❌ Overkill |

## Full Working Example

- `/tmp/gen_contract.py` — 3-page 借款契約書 with 7 clauses, property table, signature page, centered date line — all using inline underline + table_row technique.
- `/home/ysga1/借款契約書.pdf` — Generated output: dashed placeholders (`＿＿＿＿`) replaced with real PDF underlines (0.4mm solid lines), 3 pages A4, cwTeXKai font.
