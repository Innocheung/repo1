from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_font(run, size=12, bold=False, east='宋体', latin='Times New Roman', italic=False):
    run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    rf.set(qn('w:eastAsia'), east); rf.set(qn('w:ascii'), latin); rf.set(qn('w:hAnsi'), latin)


def fmt(p, align=None, first_indent=True, before=0, after=0, line=1.5):
    pf = p.paragraph_format
    if align is not None: pf.alignment = align
    pf.first_line_indent = Pt(24) if first_indent else Pt(0)
    pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = line


class Report:
    def __init__(self, doc):
        self.d = doc

    def h1(self, text):
        p = self.d.add_paragraph(); fmt(p, first_indent=False, before=12, after=6)
        set_font(p.add_run(text), 15, True, east='黑体'); return p

    def h2(self, text):
        p = self.d.add_paragraph(); fmt(p, first_indent=False, before=6, after=3)
        set_font(p.add_run(text), 13, True, east='黑体'); return p

    def para(self, text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = self.d.add_paragraph(); fmt(p, align=align, first_indent=indent)
        # simple markup: _{...} subscript, ^{...} superscript
        import re
        for tok in re.split(r'(_\{[^}]*\}|\^\{[^}]*\})', text):
            if not tok: continue
            if tok.startswith('_{'):
                r = p.add_run(tok[2:-1]); set_font(r, 12); r.font.subscript = True
            elif tok.startswith('^{'):
                r = p.add_run(tok[2:-1]); set_font(r, 12); r.font.superscript = True
            else:
                set_font(p.add_run(tok), 12)
        return p

    def eq(self, text, no):
        p = self.d.add_paragraph(); fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False)
        import re
        for tok in re.split(r'(_\{[^}]*\}|\^\{[^}]*\})', text):
            if not tok: continue
            if tok[:2] in ('_{', '^{'):
                r = p.add_run(tok[2:-1]); set_font(r, 12, italic=False)
                if tok[0] == '_': r.font.subscript = True
                else: r.font.superscript = True
            else:
                set_font(p.add_run(tok), 12)
        set_font(p.add_run(f'\t\t（{no}）'), 12)
        return p

    def fig(self, path, caption, width_cm=15.5):
        p = self.d.add_paragraph(); fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False, line=1.0)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Cm(width_cm))
        c = self.d.add_paragraph(); fmt(c, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False, after=6)
        set_font(c.add_run(caption), 10.5, east='宋体')

    def table(self, caption, rows, widths=None, total=15.5, fs=10.5):
        if widths is None:
            # width proportional to longest text in each column (CJK counts double)
            wl = lambda x: sum(2 if ord(ch) > 255 else 1 for ch in str(x))
            L = [max([0.6 * wl(rows[0][j])] + [wl(r[j]) for r in rows[1:]]) for j in range(len(rows[0]))]
            L = [max(4, min(l, 40)) for l in L]
            widths = [total * l / sum(L) for l in L]
        c = self.d.add_paragraph(); fmt(c, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False, before=6)
        c.paragraph_format.keep_with_next = True
        set_font(c.add_run(caption), 10.5, east='宋体')
        t = self.d.add_table(rows=len(rows), cols=len(rows[0]))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        # three-line table: thick top/bottom, thin rule under header
        tblPr = t._tbl.tblPr
        b = OxmlElement('w:tblBorders')
        for edge, sz in (('top', 12), ('bottom', 12), ('left', 0), ('right', 0), ('insideH', 0), ('insideV', 0)):
            e = OxmlElement(f'w:{edge}')
            e.set(qn('w:val'), 'single' if sz else 'nil'); e.set(qn('w:sz'), str(sz)); e.set(qn('w:color'), '000000')
            b.append(e)
        tblPr.append(b)
        for cell in t.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr(); cb = OxmlElement('w:tcBorders')
            e = OxmlElement('w:bottom'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '6'); e.set(qn('w:color'), '000000')
            cb.append(e); tcPr.append(cb)
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                pass
            for j, v in enumerate(r):
                cell = t.cell(i, j); cell.text = ''
                p = cell.paragraphs[0]; fmt(p, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False, line=1.15)
                p.paragraph_format.keep_with_next = i < len(rows) - 1
                import re as _re
                for tok in _re.split(r'(_\{[^}]*\}|\^\{[^}]*\})', str(v)):
                    if not tok: continue
                    if tok[:2] in ('_{', '^{'):
                        rr = p.add_run(tok[2:-1]); set_font(rr, fs, bold=(i == 0))
                        if tok[0] == '_': rr.font.subscript = True
                        else: rr.font.superscript = True
                    else:
                        set_font(p.add_run(tok), fs, bold=(i == 0))
                cell.width = Cm(widths[j])
            trPr = t.rows[i]._tr.get_or_add_trPr(); cs = OxmlElement('w:cantSplit'); trPr.append(cs)
        t.autofit = False
        tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), str(int(sum(widths) / 2.54 * 1440))); tw.set(qn('w:type'), 'dxa')
        old = tblPr.find(qn('w:tblW'))
        if old is not None: tblPr.remove(old)
        tblPr.append(tw)
        lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
        for j, col in enumerate(t.columns): col.width = Cm(widths[j])
        order = ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize', 'tblStyleColBandSize',
                 'tblW', 'jc', 'tblCellSpacing', 'tblInd', 'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook']
        kids = list(tblPr)
        for k in kids: tblPr.remove(k)
        for k in sorted(kids, key=lambda e: order.index(e.tag.split('}')[1]) if e.tag.split('}')[1] in order else 99):
            tblPr.append(k)
        sp = self.d.add_paragraph(); fmt(sp, first_indent=False, line=1.0)
        return t

    def pagebreak(self):
        p = self.d.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)
