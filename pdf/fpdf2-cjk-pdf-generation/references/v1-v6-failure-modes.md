# v1–v6 Failure Modes — CJK fpdf2 Layout Iteration

記錄 2026-07-07 生成法律分析 PDF 時六次迭代的失敗模式與最終解法。

## 迭代一覽

| 版本 | 方法 | 結果 | 根因 |
|:----:|:-----|:-----|:------|
| v1 | `cell(W)` + `multi_cell(0)` 同 Y | ❌ 重疊 | multi_cell(0) 第二行起 x 跳回 LMARGIN |
| v2 | multi_cell 兩行同 Y | ❌ 重疊 | X 範圍重疊 |
| v3 | `write()` 流式 | ❌ 溢排 | CJK 行寬計算錯誤 |
| v4 | `cell(W)` + `multi_cell(W_fixed)` 同 Y | ❌ 溢排 | CJK 超出 cell 邊界 |
| v5 | multi_cell 兩行不同 Y | ✅ 零重疊 | 不同 Y，X/Y 皆不交錯 |
| v6 | + G3 引用格式 | ✅ 完整版 | 每章末【本段資料來源】 |

## 唯一正確方法

```python
def item(label, body):
    need(35)
    pdf.set_x(INDENT)
    pdf.multi_cell(0, LH, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(INDENT + 4)
    pdf.multi_cell(0, LH, body, new_x="LMARGIN", new_y="NEXT")
```

## 失敗方法（永不使用）

- `cell(W)` + `multi_cell(0)` — multi_cell 第二行回到 LMARGIN，重疊
- `cell(W)` + `multi_cell(W_fixed)` — CJK 超出 cell 固定寬
- `write()` — CJK 溢排
- 兩個 `multi_cell(0)` 同 Y — X 範圍重疊

## 驗證

```bash
pdftoppm -png -r 200 output.pdf /tmp/vfy
python3 -c "
from PIL import Image; import numpy as np
for p in range(1, 6):
    img = Image.open(f'/tmp/vfy-{p}.png')
    arr = np.array(img.convert('L'))
    ov = sum(1 for y in range(0,arr.shape[0],2) if 0.55<(arr[y,20:arr.shape[1]-20]<80).mean()<=0.85)
    print(f'p{p}: {\"✅\" if ov<=5 else \"❌\"}')
"
```
