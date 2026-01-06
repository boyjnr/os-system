from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

def draw_header(c, W, H, m, title, os_code=None, now_str=None): pass
def draw_footer(c, W, H, m): pass
def money(v): 
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def watermark(c, W, H, text): pass
