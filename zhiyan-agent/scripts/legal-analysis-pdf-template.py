#!/usr/bin/env python3
"""
法律深度研究 PDF 生成樣版 script。

使用方式：
  1. 複製此檔案為 generate_<主題>_pdf.py
  2. 修改 section / sub_item 內容
  3. 執行: python3 <檔案>

內建排版保護：
  - check_space() 防止子項目跨頁斷層
  - sub_item() 兩行 multi_cell 避免 CJK 重疊
  - law_box() 法條引文框，動態高度
  - table() 通用表格
  - 自動確保最後一頁至少半頁滿

字型路徑（Ubuntu 24.04 + fonts-noto-cjk）：
  NotoSerifCJK-Regular.ttc
  NotoSerifCJK-Bold.ttc

快出：python3 generate_<主題>_pdf.py && ls -lh <輸出>.pdf
"""

from fpdf import FPDF
from datetime import date

today = date.today().isoformat()

# ── 排版常數（依需求調整） ─────────────────────────────────
FONT_BODY = 9.5
LINE_H = 5.8
MARGIN_L = 20
INDENT = 34
GAP = 1
NAVY = (20, 40, 85)          # 主色
DARK = (60, 60, 60)          # 內文
GRAY = (140, 140, 140)       # 次要


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('NotoSerif', '', 7.5)
            self.set_text_color(GRAY)
            self.cell(0, 6, '智研法律 AI 系統  •  {報告主題}', align='L')
            self.ln(10)

    def footer(self):
        self.set_y(-14)
        self.set_font('NotoSerif', '', 7.5)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f'— 第 {self.page_no()} 頁 —', align='C')


pdf = PDF('P', 'mm', 'A4')
pdf.add_font('NotoSerif', '', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
pdf.add_font('NotoSerif', 'B', '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc')
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_margin(MARGIN_L)


# ── 排版輔助函數（直接複製使用） ───────────────────────────

def check_space(mm=30):
    """剩餘空間不足時換頁，防止子項目跨頁斷層"""
    if 297 - 18 - pdf.get_y() < mm:
        pdf.add_page()


def section(num, title):
    """章節標題：藏青底白字編號 + 粗體標題"""
    check_space(18)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('NotoSerif', 'B', 9)
    pdf.cell(8, 7, num, fill=True, align='C')
    pdf.set_text_color(*NAVY)
    pdf.set_font('NotoSerif', 'B', 12)
    pdf.cell(4)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(GAP)


def write_item(label, body, indent=INDENT):
    """流式子項目：Label + Body 用 write() 同行自然換行，零重疊"""
    check_space(35)
    y0 = pdf.get_y()
    pdf.set_x(indent)
    pdf.set_font('NotoSerif', 'B', FONT_BODY)
    pdf.set_text_color(*NAVY)
    pdf.write(LINE_H, label + '  ')
    pdf.set_font('NotoSerif', '', FONT_BODY)
    pdf.set_text_color(*DARK)
    pdf.write(LINE_H, body)
    if pdf.get_y() == y0:
        pdf.ln(LINE_H)
    pdf.ln(GAP)


def sub_item(label, body):
    \"\"\"子項目：粗體藍標籤 → 縮排內文（兩行 multi_cell 防重疊，備用）\"\"\"
    check_space(30)
    pdf.set_x(INDENT)
    pdf.set_font('NotoSerif', 'B', FONT_BODY)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, LINE_H, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(INDENT + 4)
    pdf.set_font('NotoSerif', '', FONT_BODY)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, LINE_H, body, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(GAP)


def body_text(text):
    """純內文段落"""
    check_space(10)
    pdf.set_x(INDENT)
    pdf.set_font('NotoSerif', '', FONT_BODY)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, LINE_H, text, new_x="LMARGIN", new_y="NEXT")


def bold_text(text, color=DARK):
    """粗體內文（用於結論重點）"""
    check_space(10)
    pdf.set_x(INDENT)
    pdf.set_font('NotoSerif', 'B', FONT_BODY)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, LINE_H, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(GAP)


def divider():
    """淺灰分隔線"""
    check_space(8)
    pdf.set_draw_color(215, 215, 215)
    pdf.set_line_width(0.2)
    y = pdf.get_y()
    pdf.line(MARGIN_L, y, 210 - MARGIN_L, y)
    pdf.ln(2)


def law_box(text, title, bg=(245, 245, 250), bc=(130, 150, 180),
            tc=NAVY, tc2=(55, 55, 70), h_pad=3):
    """法條引文框（動態高度）"""
    check_space(45)
    bx = INDENT
    by = pdf.get_y()
    pdf.set_xy(bx + 3, by + 2)
    pdf.set_font('NotoSerif', 'B', 8.5)
    pdf.set_text_color(*tc)
    pdf.cell(0, 5, title)
    pdf.set_xy(bx + 3, pdf.get_y() + 1)
    pdf.set_font('NotoSerif', '', 8.5)
    pdf.set_text_color(*tc2)
    pdf.multi_cell(152, 4.5, text, new_x="LMARGIN", new_y="NEXT")
    ey = pdf.get_y() + h_pad
    pdf.set_fill_color(*bg)
    pdf.set_draw_color(*bc)
    pdf.set_line_width(0.3)
    pdf.rect(bx, by, 158, ey - by)
    pdf.set_y(ey + GAP)


def table(headers, rows, col_w):
    """通用表格（navy 表頭 + 交替行背景）"""
    pdf.set_x(MARGIN_L)
    pdf.set_fill_color(*NAVY)
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
        pdf.set_text_color(*DARK)
        pdf.set_font('NotoSerif', 'B', 8.5)
        pdf.cell(col_w[0], 7, row[0], border=1, fill=True)
        pdf.set_font('NotoSerif', '', 8.5)
        for j in range(1, len(row)):
            pdf.cell(col_w[j], 7, row[j], border=1, fill=True,
                     align='C' if j == 1 else 'L')
        pdf.ln()


# ═══════════════════════ 正文開始 ═══════════════════════

# 封面
pdf.add_page()
pdf.ln(48)
pdf.set_font('NotoSerif', 'B', 28)
pdf.set_text_color(*NAVY)
pdf.multi_cell(0, 15, '文件主標題\n副標題', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)
pdf.set_draw_color(*NAVY)
pdf.set_line_width(0.6)
pdf.line(55, pdf.get_y(), 155, pdf.get_y())
pdf.ln(10)
pdf.set_font('NotoSerif', '', 11)
pdf.set_text_color(90, 90, 90)
pdf.multi_cell(0, 7, '關鍵字標籤', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(35)
pdf.set_font('NotoSerif', '', 9)
pdf.set_text_color(130, 130, 130)
pdf.cell(0, 6, today, align='C', new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, '智研法律 AI 系統', align='C', new_x="LMARGIN", new_y="NEXT")

# 摘要框
pdf.add_page()
bx, by, bw = 18, pdf.get_y(), 174
pdf.set_fill_color(240, 246, 255)
pdf.set_draw_color(*NAVY)
pdf.set_line_width(0.4)
pdf.set_xy(bx + 4, by + 2)
pdf.set_font('NotoSerif', 'B', 10)
pdf.set_text_color(*NAVY)
pdf.cell(0, 7, '摘  要')
pdf.set_xy(bx + 4, pdf.get_y() + 1)
pdf.set_font('NotoSerif', '', 9.5)
pdf.set_text_color(55, 55, 55)
pdf.multi_cell(bw - 8, LINE_H,
    '摘要文字…')
ey = pdf.get_y()
pdf.rect(bx, by, bw, ey - by + 4)
pdf.set_y(ey + 6)

# 章節範例
section('1', '第一章範例')
sub_item('1.1 子項目', '子項目內文。引用附來源 (全國法規資料庫)。')

# 法條框範例
law_box(
    '"條文內容範例"',
    title='法條名稱 — 引用框：',
    bg=(245, 245, 250), bc=(130, 150, 180),
    tc=NAVY, tc2=(55, 55, 70),
)

# 表格範例
table(
    ['主題', '關注程度', '法條框架', '參考來源'],
    [('項目一', '高', '土法§79-1', '全國法規資料庫'),
     ('項目二', '高', '刑§214', '全國法規資料庫')],
    [32, 28, 68, 62]
)

body_text('結語文字。')

# 確保最後一頁至少半頁
final_remain = 297 - 18 - pdf.get_y()
if pdf.page_no() >= 2 and final_remain < 130:
    pdf.ln(130 - final_remain)

# 免責聲明
pdf.set_draw_color(180, 180, 180)
pdf.set_line_width(0.3)
pdf.line(MARGIN_L, pdf.get_y(), 210 - MARGIN_L, pdf.get_y())
pdf.ln(2)
pdf.set_font('NotoSerif', '', 7.5)
pdf.set_text_color(GRAY)
pdf.multi_cell(0, 4,
    '免責聲明：本文由智研法律 AI 系統生成，僅供法律知識參考，不構成具體法律意見。'
    '如有個案需求，請諮詢合格律師。報告中引用之法條以全國法規資料庫最新版本為準。')
pdf.cell(0, 4, today, align='C', new_x="LMARGIN", new_y="NEXT")

output = '/home/ysga1/自訂主題分析報告.pdf'
pdf.output(output)
print(f'PDF: {output}')
print(f'頁數: {pdf.page_no()}')
