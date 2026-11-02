import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, sys, copy, numpy as np
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docutil import Report, set_font, fmt

TITLE = '三叶片扭曲型垂直轴风力机不同风速工况下气动性能与尾流场数值模拟'
SRC = '../doc/in.docx'
OUT = sys.argv[1]
W = '.'

cases = [json.load(open(f'{W}/case_U{u}.json')) for u in (4, 6, 8, 10)]
wake = json.load(open(f'{W}/wake_stats.json'))
static = json.load(open(f'{W}/static.json'))
analysis = json.load(open(f'{W}/analysis.json'))

doc = Document(SRC)
# ---- fill title on cover table ----
tbl = doc.tables[0]
cell = tbl.cell(2, 2)
for p in cell.paragraphs[1:]:
    p._element.getparent().remove(p._element)
p = cell.paragraphs[0]
for r in p.runs: r.text = ''
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run(TITLE), 12, True, east='宋体')

R = Report(doc)
R.pagebreak()
# report title
p = doc.add_paragraph(); fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False, after=12)
set_font(p.add_run(TITLE), 16, True, east='黑体')

for sec in analysis['sections']:
    kind = sec[0]
    if kind == 'h1': R.h1(sec[1])
    elif kind == 'h2': R.h2(sec[1])
    elif kind == 'p': R.para(sec[1])
    elif kind == 'eq': R.eq(sec[1], sec[2])
    elif kind == 'fig': R.fig(sec[1], sec[2], sec[3] if len(sec) > 3 else 15.5)
    elif kind == 'table': R.table(sec[1], sec[2], widths=(sec[3] if len(sec) > 3 else None), fs=(9 if len(sec[2][0]) > 7 else 10.5))
    elif kind == 'ref':
        for i, t in enumerate(sec[1], 1):
            q = doc.add_paragraph(); fmt(q, first_indent=False, line=1.25)
            q.paragraph_format.left_indent = Pt(24); q.paragraph_format.first_line_indent = Pt(-24)
            set_font(q.add_run(f'[{i}] {t}'), 10.5)
    elif kind == 'pb': R.pagebreak()

doc.save(OUT)
print('saved', OUT)
