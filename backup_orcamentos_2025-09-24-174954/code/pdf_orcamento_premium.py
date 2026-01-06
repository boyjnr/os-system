from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from pdf_theme import draw_header, draw_footer, money, watermark

def gerar_pdf_orcamento_premium(orc, os_dados, destino, wa_link=None):
    c = canvas.Canvas(destino, pagesize=A4)
    W,H = A4; m = 18*mm
    now = datetime.now().strftime('%d/%m/%Y %H:%M')

    draw_header(c,W,H,m,'Proposta de Orçamento — TI Extremo', os_dados.get('os_code'), now)

    y = H-72*mm
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold', 11)
    c.drawString(m,y, f"Orçamento #{orc['id']}  •  Status: {orc['status']}"); y-=9*mm
    c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#374151'))
    c.drawString(m,y, f"Cliente: {os_dados.get('cliente','-')}"); y-=5*mm
    c.drawString(m,y, f"Telefone: {os_dados.get('telefone','-')}"); y-=8*mm

    # Cabeçalho da tabela
    c.setFillColor(colors.HexColor('#f3f4f6')); c.rect(m,y-9*mm,W-2*m,9*mm,0,1)
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold',9)
    c.drawString(m+3,y-4,"Descrição"); c.drawRightString(W-m-55,y-4,"Qtd")
    c.drawRightString(W-m-5-80,y-4,"V. Unit"); c.drawRightString(W-m-5,y-4,"Total"); y-=9*mm

    # Itens (zebra)
    c.setFont('Helvetica',9)
    for i,it in enumerate(orc['itens']):
        if i%2: c.setFillColor(colors.HexColor('#fafafa')); c.rect(m,y-9*mm,W-2*m,9*mm,0,1)
        c.setFillColor(colors.black)
        c.drawString(m+3,y-4, it['desc'][:90])
        c.drawRightString(W-m-55,y-4, f"{it['qtd']}")
        c.drawRightString(W-m-5-80,y-4, money(it['preco']))
        c.drawRightString(W-m-5,y-4, money(it['qtd']*it['preco']))
        y-=9*mm
        if y<50*mm:
            c.showPage()
            draw_header(c,W,H,m,'Proposta de Orçamento — TI Extremo', os_dados.get('os_code'), now)
            y=H-40*mm

    # Totais
    y-=3*mm; c.setFont('Helvetica-Bold',9); c.setFillColor(colors.black)
    c.drawRightString(W-m-5-80,y-2,"Subtotal:"); c.drawRightString(W-m-5,y-2,money(orc['subtotal'])); y-=6*mm
    c.setFont('Helvetica-Bold',9); c.setFillColor(colors.HexColor('#6b7280'))
    c.drawRightString(W-m-5-80,y-2,"Desconto:"); c.drawRightString(W-m-5,y-2,money(orc['desconto'])); y-=9*mm
    c.setFont('Helvetica-Bold',12); c.setFillColor(colors.black)
    c.drawRightString(W-m-5-80,y,"Total:"); c.drawRightString(W-m-5,y,money(orc['total'])); y-=12*mm

    # Condições + WhatsApp
    c.setFont('Helvetica-Bold',10); c.setFillColor(colors.black)
    c.drawString(m,y,"Condições & Prazo"); y-=5*mm
    c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#374151'))
    c.drawString(m,y, (orc.get('condicoes') or 'Validade: 5 dias. Pagamento: PIX/cartão.')); y-=8*mm
    if wa_link:
        c.setFillColor(colors.HexColor('#2563eb')); c.setFont('Helvetica-Bold',9)
        c.drawString(m,y,"Aprovar pelo WhatsApp: "); 
        c.linkURL(wa_link,(m+120,y-1,m+380,y+9)); 
        y-=8*mm

    draw_footer(c,W,H,m)
    if orc['status'] in ('PENDENTE','APROVADO'):
        watermark(c,W,H,orc['status'])
    c.showPage(); c.save()
