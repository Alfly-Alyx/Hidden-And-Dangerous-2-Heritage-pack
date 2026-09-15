from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Flowable, ListFlowable, ListItem, NextPageTemplate
)

ROOT = Path(r"D:\Projets\GITHUB\H&D2")
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)

FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
FONT_SEMI = Path(r"C:\Windows\Fonts\seguisb.ttf")
pdfmetrics.registerFont(TTFont("UI", str(FONT)))
pdfmetrics.registerFont(TTFont("UI-Bold", str(FONT_BOLD)))
pdfmetrics.registerFont(TTFont("UI-Semi", str(FONT_SEMI if FONT_SEMI.exists() else FONT_BOLD)))

NAVY = colors.HexColor("#17243A")
NAVY_2 = colors.HexColor("#233A5E")
RED = colors.HexColor("#B83A3A")
GOLD = colors.HexColor("#D6A84B")
INK = colors.HexColor("#1C2430")
MUTED = colors.HexColor("#647184")
PALE = colors.HexColor("#E9EEF5")
GREEN = colors.HexColor("#39725B")
WHITE = colors.white
PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
TOP = 18 * mm
BOTTOM = 17 * mm

styles = {
    "cover_kicker": ParagraphStyle("cover_kicker", fontName="UI-Semi", fontSize=10, leading=13, textColor=GOLD, spaceAfter=8, tracking=1.1),
    "cover_title": ParagraphStyle("cover_title", fontName="UI-Bold", fontSize=30, leading=33, textColor=WHITE, spaceAfter=14),
    "cover_sub": ParagraphStyle("cover_sub", fontName="UI", fontSize=13, leading=18, textColor=colors.HexColor("#D9E1EC"), spaceAfter=16),
    "cover_meta": ParagraphStyle("cover_meta", fontName="UI", fontSize=9.5, leading=14, textColor=colors.HexColor("#BCC7D6")),
    "h1": ParagraphStyle("h1", fontName="UI-Bold", fontSize=22, leading=25, textColor=NAVY, spaceAfter=8, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="UI-Semi", fontSize=14, leading=18, textColor=NAVY_2, spaceBefore=8, spaceAfter=5, keepWithNext=True),
    "h3": ParagraphStyle("h3", fontName="UI-Semi", fontSize=11, leading=14, textColor=RED, spaceBefore=5, spaceAfter=3, keepWithNext=True),
    "body": ParagraphStyle("body", fontName="UI", fontSize=9.2, leading=13.2, textColor=INK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="UI", fontSize=7.6, leading=10.2, textColor=MUTED, spaceAfter=3),
    "note": ParagraphStyle("note", fontName="UI", fontSize=8.6, leading=12, textColor=INK),
    "table": ParagraphStyle("table", fontName="UI", fontSize=7.5, leading=9.7, textColor=INK),
    "table_head": ParagraphStyle("table_head", fontName="UI-Semi", fontSize=7.7, leading=9.8, textColor=WHITE),
    "step_num": ParagraphStyle("step_num", fontName="UI-Bold", fontSize=16, leading=18, textColor=WHITE, alignment=TA_CENTER),
    "step": ParagraphStyle("step", fontName="UI", fontSize=9.1, leading=12.8, textColor=INK),
    "source": ParagraphStyle("source", fontName="UI", fontSize=7.1, leading=9.2, textColor=MUTED, wordWrap="CJK", spaceAfter=3),
}

def clean(s):
    return s.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")

def P(text, style="body"):
    return Paragraph(clean(text), styles[style])

def bullet(items):
    return ListFlowable(
        [ListItem(P(i, "body"), leftIndent=0) for i in items],
        bulletType="bullet", bulletColor=RED, bulletFontName="UI-Bold",
        bulletFontSize=7, leftIndent=14, bulletOffsetY=2, spaceAfter=5
    )

def number_steps(items):
    rows = []
    for i, value in enumerate(items, 1):
        badge = Table([[P(str(i), "step_num")]], colWidths=[8*mm], rowHeights=[8*mm],
            style=TableStyle([("BACKGROUND",(0,0),(-1,-1),RED),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        rows.append([badge, P(value, "step")])
    result = Table(rows, colWidths=[10*mm, 158*mm], hAlign="LEFT")
    result.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)
    ]))
    return result

def info_box(title, text, color=PALE):
    result = Table([[P(title,"h3")],[P(text,"note")]], colWidths=[168*mm], hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),color),("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#C8D2DF")),
        ("LINEBEFORE",(0,0),(0,-1),4,RED),("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,0),6),
        ("BOTTOMPADDING",(0,-1),(-1,-1),7)
    ]))
    return result

def table(data, widths, header=True):
    converted = []
    for r, row in enumerate(data):
        converted.append([cell if isinstance(cell, Flowable) else P(str(cell), "table_head" if header and r == 0 else "table") for cell in row])
    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#CBD3DD")),
        ("ROWBACKGROUNDS",(0,1 if header else 0),(-1,-1),[WHITE,colors.HexColor("#F7F9FB")])
    ]
    if header:
        cmds.append(("BACKGROUND",(0,0),(-1,0),NAVY_2))
    result.setStyle(TableStyle(cmds))
    return result

def section(story, number, title, subtitle=None):
    story.append(P(f"{number}  {title}","h1"))
    if subtitle:
        story.append(P(subtitle))
    story.append(Spacer(1,2*mm))

def cover(story, kicker, title, subtitle, meta):
    story.append(Spacer(1,31*mm))
    story.append(P(kicker.upper(),"cover_kicker"))
    story.append(P(title,"cover_title"))
    story.append(P(subtitle,"cover_sub"))
    story.append(Spacer(1,58*mm))
    story.append(P(meta,"cover_meta"))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    canvas.setFillColor(RED)
    canvas.rect(0,PAGE_H-10*mm,PAGE_W,10*mm,fill=1,stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(MARGIN_X,25*mm,32*mm,2.2*mm,fill=1,stroke=0)
    canvas.setStrokeColor(colors.HexColor("#445672"))
    for y in (55,65,75):
        canvas.line(MARGIN_X,y*mm,PAGE_W-MARGIN_X,y*mm)
    canvas.restoreState()

def body_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0,PAGE_H-8*mm,PAGE_W,8*mm,fill=1,stroke=0)
    canvas.setFont("UI-Semi",7)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X,9*mm,doc._doc_label)
    canvas.drawRightString(PAGE_W-MARGIN_X,9*mm,str(doc.page))
    canvas.setStrokeColor(colors.HexColor("#D7DDE5"))
    canvas.line(MARGIN_X,13*mm,PAGE_W-MARGIN_X,13*mm)
    canvas.restoreState()

class HD2Doc(BaseDocTemplate):
    def __init__(self, filename, label):
        super().__init__(filename,pagesize=A4,leftMargin=MARGIN_X,rightMargin=MARGIN_X,topMargin=TOP,bottomMargin=BOTTOM,title=label,author="HD2 Community Pack")
        self._doc_label = label
        frame = Frame(MARGIN_X,BOTTOM,PAGE_W-2*MARGIN_X,PAGE_H-BOTTOM-TOP,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover",frames=[frame],onPage=cover_page),
            PageTemplate(id="body",frames=[frame],onPage=body_page)
        ])

class Africa4Map(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 168*mm
        self.height = 82*mm
    def draw(self):
        c,w,h = self.canv,self.width,self.height
        c.saveState()
        c.setFillColor(colors.HexColor("#F5EAD3"))
        c.roundRect(0,0,w,h,3*mm,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor("#7A6549"))
        c.setLineWidth(3)
        c.rect(15*mm,9*mm,138*mm,63*mm,fill=0,stroke=1)
        c.setLineWidth(1)
        c.setFillColor(colors.HexColor("#D8C59D"))
        for x,y,bw,bh in [(23,14,31,17),(60,13,22,14),(90,14,26,17),(24,42,26,20),(61,39,30,24),(101,40,39,21)]:
            c.rect(x*mm,y*mm,bw*mm,bh*mm,fill=1,stroke=1)
        c.setFillColor(colors.HexColor("#B99F70"))
        c.circle(105*mm,47*mm,7*mm,fill=1,stroke=1)
        for label,(x,y,col) in {"A":(55*mm,22*mm,RED),"B":(105*mm,43*mm,GOLD),"C":(120*mm,61*mm,GREEN)}.items():
            c.setFillColor(col)
            c.circle(x,y,5*mm,fill=1,stroke=0)
            c.setFillColor(WHITE)
            c.setFont("UI-Bold",10)
            c.drawCentredString(x,y-3,label)
        c.setFillColor(NAVY)
        c.setFont("UI-Semi",7.5)
        c.drawString(18*mm,75*mm,"NORD")
        c.line(30*mm,73*mm,30*mm,78*mm)
        c.line(30*mm,78*mm,28*mm,75.5*mm)
        c.line(30*mm,78*mm,32*mm,75.5*mm)
        c.setFont("UI",7)
        c.drawString(18*mm,4*mm,"Schéma d'orientation - enceinte principale, pas à l'échelle")
        c.restoreState()