#!/usr/bin/env bash
set -euo pipefail
cd ~/os-system

echo "[1/3] Backup rápido…"
mkdir -p backups_rapidos
cp -a main.py pdf_orcamento_premium.py 2>/dev/null backups_rapidos/ || true

echo "[2/3] Criando pdf_orcamento_match_os.py (usa header/rodapé da OS, sem tocar na OS)…"
cat > pdf_orcamento_match_os.py <<'PY'
# Gera PDF de Orçamento usando o MESMO padrão da OS (sem alterar a OS).
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

# 1) Tentamos importar header/rodapé da sua OS
_OS_HDR = None; _OS_FTR = None
try:
    from pdf_os_premium import draw_header as _OS_HDR, draw_footer as _OS_FTR  # se existirem
except Exception:
    _OS_HDR = None; _OS_FTR = None

# 2) Fallback (visual próximo ao da OS)
def _fallback_header(c, W, H, m, title, os_code=None, now_str=None):
    c.setFillColor(colors.HexColor('#f97316')); c.rect(0, H-16*mm, W, 16*mm, 0, 1)
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-12*mm, 'T.I Extremo — Soluções em TI Premium')
    c.setFillColor(colors.HexColor('#0f172a')); c.setFont('Helvetica-Bold', 10)
    if os_code: c.drawString(m, H-28*mm, os_code)
    c.setFillColor(colors.HexColor('#6b7280')); c.setFont('Helvetica', 8.5)
    if now_str: c.drawString(m, H-32*mm, f'Data: {now_str}')
    c.setFillColor(colors.HexColor('#0f172a')); c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-45*mm, title)

def _fallback_footer(c, W, H, m):
    c.setStrokeColor(colors.HexColor('#e5e7eb')); c.line(m, 16*mm, W-m, 16*mm)
    c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#0f172a'))
    c.drawCentredString(W/2, 10*mm, '★ 1 ano de garantia nos serviços')
    c.drawCentredString(W/2, 6*mm, 'Av. Eng. Luís C. Berrini, 1748 — (11) 98844-0181 — orlando@tiextremo.com.br — www.tiextremo.com.br')

def _money(v): 
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_pdf_orcamento_match_os(orc:dict, os_dados:dict, destino:str, wa_link:str|None=None):
    c = canvas.Canvas(destino, pagesize=A4)
    W,H = A4; m = 18*mm
    now = datetime.now().strftime('%d/%m/%Y %H:%M')

    title = 'Proposta de Orçamento'
    if _OS_HDR: _OS_HDR(c, W, H, m, title, os_dados.get('os_code'), now)  # usa header da OS
    else:       _fallback_header(c, W, H, m, title, os_dados.get('os_code'), now)

    y = H-72*mm
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold', 11)
    c.drawString(m,y, f"Orçamento #{orc.get('id','-')}  •  Status: {orc.get('status','-')}"); y-=9*mm
    c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#374151'))
    c.drawString(m,y, f"Cliente: {os_dados.get('cliente','-')}"); y-=5*mm
    c.drawString(m,y, f"Telefone: {os_dados.get('telefone','-')}"); y-=8*mm

    # Tabela
    c.setFillColor(colors.HexColor('#f3f4f6')); c.rect(m,y-9*mm,W-2*m,9*mm,0,1)
    c.setFillColor(colors.black); c.setFont('Helvetica-Bold',9)
    c.drawString(m+3,y-4,"Descrição"); c.drawRightString(W-m-55,y-4,"Qtd")
    c.drawRightString(W-m-5-80,y-4,"V. Unit"); c.drawRightString(W-m-5,y-4,"Total"); y-=9*mm

    c.setFont('Helvetica',9)
    itens = orc.get('itens') or []
    for i,it in enumerate(itens):
        if i%2: c.setFillColor(colors.HexColor('#fafafa')); c.rect(m,y-9*mm,W-2*m,9*mm,0,1)
        c.setFillColor(colors.black)
        desc = (it.get('desc') or '')[:90]
        qtd  = it.get('qtd', 1)
        preco= it.get('preco', 0.0)
        c.drawString(m+3,y-4, desc)
        c.drawRightString(W-m-55,y-4, f"{qtd}")
        c.drawRightString(W-m-5-80,y-4, _money(preco))
        c.drawRightString(W-m-5,y-4, _money(qtd*preco))
        y-=9*mm
        if y<50*mm:
            c.showPage()
            if _OS_HDR: _OS_HDR(c, W, H, m, title, os_dados.get('os_code'), now)
            else:       _fallback_header(c, W, H, m, title, os_dados.get('os_code'), now)
            y = H-40*mm

    # Totais
    subtotal = orc.get('subtotal', 0.0); desconto = orc.get('desconto', 0.0); total = orc.get('total', subtotal-desconto)
    y-=3*mm; c.setFont('Helvetica-Bold',9); c.setFillColor(colors.black)
    c.drawRightString(W-m-5-80,y-2,"Subtotal:"); c.drawRightString(W-m-5,y-2,_money(subtotal)); y-=6*mm
    c.setFont('Helvetica-Bold',9); c.setFillColor(colors.HexColor('#6b7280'))
    c.drawRightString(W-m-5-80,y-2,"Desconto:"); c.drawRightString(W-m-5,y-2,_money(desconto)); y-=9*mm
    c.setFont('Helvetica-Bold',12); c.setFillColor(colors.black)
    c.drawRightString(W-m-5-80,y,"Total:"); c.drawRightString(W-m-5,y,_money(total)); y-=12*mm

    # Condições + WhatsApp (opcional)
    c.setFont('Helvetica-Bold',10); c.setFillColor(colors.black)
    c.drawString(m,y,"Condições & Prazo"); y-=5*mm
    c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#374151'))
    c.drawString(m,y, (orc.get('condicoes') or 'Validade: 5 dias. Pagamento: PIX/cartão.')); y-=8*mm
    if wa_link:
        c.setFillColor(colors.HexColor('#2563eb')); c.setFont('Helvetica-Bold',9)
        c.drawString(m,y,"Aprovar pelo WhatsApp: "); 
        c.linkURL(wa_link,(m+120,y-1,m+380,y+9)); 
        y-=8*mm

    # Rodapé
    if _OS_FTR: _OS_FTR(c, W, H, m)
    else:       _fallback_footer(c, W, H, m)

    c.showPage(); c.save()
PY

echo "[3/3] Apontando endpoint para o gerador que segue o padrão da OS…"
sed -i.bak 's/from pdf_orcamento_premium import gerar_pdf_orcamento_premium/from pdf_orcamento_match_os import gerar_pdf_orcamento_match_os/' main.py 2>/dev/null || true
if grep -q "def pdf_orcamento(" main.py; then
  sed -i 's/gerar_pdf_orcamento_premium(orc, os_dados, destino, wa_link=wa)/gerar_pdf_orcamento_match_os(orc, os_dados, destino, wa_link=wa)/' main.py || true
fi

echo "Feito! O orçamento agora tenta usar o MESMO header/rodapé da OS (sem alterar a OS)."
