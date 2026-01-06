from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

W, H = A4

def _wrap(text:str, max_w, font='Helvetica', size=9):
    tmp = canvas.Canvas(None)
    words = (text or '').split()
    lines, cur = [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if stringWidth(test, font, size) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# === CABEÇALHO IDÊNTICO À OS =================================================
def _os_like_header(c, m, os_code:str, now_str:str, title:str):
    # Barra superior laranja
    c.setFillColor(colors.HexColor('#f97316'))
    c.rect(0, H-16*mm, W, 16*mm, stroke=0, fill=1)

    # Título branco
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-12*mm, 'T.I Extremo — Soluções em TI Premium')

    # Código + Data (mesmas posições da OS)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont('Helvetica-Bold', 12)
    c.drawString(m, H-28*mm, os_code or 'OS')
    c.setFont('Helvetica', 8.5)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawString(m, H-32*mm, 'Data: ' + now_str)

    # Subtítulo/slogan (mesmo texto/posição)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(W/2, H-45*mm, 'TI Extremo — Soluções em TI Geral')
    c.setFont('Helvetica', 8.5)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawCentredString(W/2, H-48*mm, 'Na Berrini, em frente à Ponte Estaiada — excelência com preço justo')

    # Selo à direita (mesma linha)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.drawRightString(W-18*mm, H-62*mm, '4.9★ no Google — Melhor avaliada')

    # Título da página (próprio do orçamento, abaixo do cabeçalho)
    c.setFillColor(colors.HexColor('#111827'))
    c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-68*mm, title)

# === RODAPÉ IDÊNTICO À OS ====================================================
def _os_like_footer(c):
    # Destaque garantia (22mm)
    c.setFont("Helvetica-Bold", 9.4); c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(W/2, 22*mm, "★ ÚNICA assistência com 1 ano de garantia nos serviços.")

    # Endereço/contato (16mm e 12mm)
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#6b7280"))
    c.drawCentredString(W/2, 16*mm, "Av. Eng. Luís Carlos Berrini, 1748 — São Paulo–SP — (11) 98844-0181")
    c.drawCentredString(W/2, 12*mm, "orlando@tiextremo.com.br — www.tiextremo.com.br")

    # Página (12mm direita)
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#6b7280"))
    c.drawRightString(W-18*mm, 12*mm, "Página 1")

def _money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_pdf_orcamento_match_os(orc:dict, os_dados:dict, destino:str, wa_link:str|None=None):
    c = canvas.Canvas(destino, pagesize=A4)
    m = 18*mm
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    os_code = (os_dados or {}).get('os_code','OS')

    # Cabeçalho idêntico à OS
    _os_like_header(c, m, os_code, now, "Proposta de Orçamento")

    # Bloco de identificação (alinha com sua OS)
    y = H-80*mm
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(m, y, f"Orçamento #{orc.get('id','-')} • Status: {orc.get('status','-')}")
    y -= 6*mm

    c.setFillColor(colors.HexColor("#0f172a")); c.setFont("Helvetica", 9)
    c.drawString(m, y, f"Cliente: {os_dados.get('cliente','-')}"); y -= 5.2*mm
    c.drawString(m, y, f"Telefone: {os_dados.get('telefone','-')}"); y -= 9*mm

    # Tabela de itens (estilo limpo, mesma tipografia geral)
    c.setFillColor(colors.HexColor('#f3f4f6')); c.rect(m, y-9*mm, W-2*m, 9*mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor('#0f172a')); c.setFont('Helvetica-Bold',9)
    c.drawString(m+3, y-4, "Descrição")
    c.drawRightString(W-m-55, y-4, "Qtd")
    c.drawRightString(W-m-5-80, y-4, "V. Unit")
    c.drawRightString(W-m-5, y-4, "Total")
    y -= 9*mm

    c.setFont('Helvetica',9)
    itens = orc.get('itens') or []
    for i, it in enumerate(itens):
        if i%2: c.setFillColor(colors.HexColor('#fafafa')); c.rect(m, y-9*mm, W-2*m, 9*mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor('#0f172a'))
        desc = (it.get('desc') or '')[:90]
        qtd = it.get('qtd', 1)
        preco = it.get('preco', 0.0)
        c.drawString(m+3, y-4, desc)
        c.drawRightString(W-m-55, y-4, f"{qtd}")
        c.drawRightString(W-m-5-80, y-4, _money(preco))
        c.drawRightString(W-m-5, y-4, _money(qtd*preco))
        y -= 9*mm
        if y < 50*mm:
            c.showPage()
            _os_like_header(c, m, os_code, now, "Proposta de Orçamento")
            y = H-40*mm

    # Totais
    subtotal = orc.get('subtotal', 0.0); desconto = orc.get('desconto', 0.0); total = orc.get('total', subtotal-desconto)
    y -= 3*mm
    c.setFont('Helvetica-Bold',9); c.setFillColor(colors.HexColor('#0f172a'))
    c.drawRightString(W-m-5-80, y-2, "Subtotal:"); c.drawRightString(W-m-5, y-2, _money(subtotal)); y -= 6*mm
    c.setFont('Helvetica-Bold',9); c.setFillColor(colors.HexColor('#6b7280'))
    c.drawRightString(W-m-5-80, y-2, "Desconto:"); c.drawRightString(W-m-5, y-2, _money(desconto)); y -= 9*mm
    c.setFont('Helvetica-Bold',12); c.setFillColor(colors.HexColor('#0f172a'))
    c.drawRightString(W-m-5-80, y, "Total:"); c.drawRightString(W-m-5, y, _money(total)); y -= 12*mm

    # Condições + WhatsApp
    c.setFont('Helvetica-Bold',10); c.setFillColor(colors.HexColor('#111827'))
    c.drawString(m, y, "Condições & Prazo"); y -= 5*mm
    c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#0f172a'))
    c.drawString(m, y, (orc.get('condicoes') or 'Validade: 5 dias. Pagamento: PIX/cartão.')); y -= 8*mm

    if wa_link:
        c.setFillColor(colors.HexColor('#2563eb')); c.setFont('Helvetica-Bold',9)
        c.drawString(m, y, "Aprovar pelo WhatsApp: ")
        c.linkURL(wa_link, (m+120, y-1, m+380, y+9))
        y -= 8*mm

    # Rodapé idêntico à OS
    _os_like_footer(c)

    c.showPage()
    c.save()
