#!/usr/bin/env bash
set -euo pipefail
cd ~/os-system

echo "[1/5] Backup rápido…"
mkdir -p backups_rapidos
cp -a main.py templates/ pdf_*.py backups_rapidos/ 2>/dev/null || true

echo "[2/5] Criando pdf_theme.py…"
cat > pdf_theme.py <<'PY'
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

ORANGE = colors.HexColor('#f97316')
INK    = colors.HexColor('#0f172a')
MUTED  = colors.HexColor('#6b7280')

def draw_header(c, W, H, m, title, os_code=None, now_str=None):
    c.setFillColor(ORANGE); c.rect(0, H-16*mm, W, 16*mm, 0, 1)
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-12*mm, 'T.I Extremo — Soluções em TI Premium')
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 10)
    if os_code: c.drawString(m, H-28*mm, os_code)
    c.setFillColor(MUTED); c.setFont('Helvetica', 8.5)
    if now_str: c.drawString(m, H-32*mm, f'Data: {now_str}')
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 11)
    c.drawString(m, H-45*mm, title)

def draw_footer(c, W, H, m):
    c.setStrokeColor(colors.HexColor('#e5e7eb')); c.line(m, 16*mm, W-m, 16*mm)
    c.setFont('Helvetica', 8); c.setFillColor(INK)
    c.drawCentredString(W/2, 10*mm, '★ 1 ano de garantia nos serviços')
    c.drawCentredString(W/2, 6*mm, 'Av. Eng. Luís C. Berrini, 1748 — (11) 98844-0181 — orlando@tiextremo.com.br — www.tiextremo.com.br')

def money(v): 
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def watermark(c, W, H, text):
    c.saveState(); c.setFillColor(colors.HexColor('#9ca3af')); c.setFont('Helvetica-Bold', 56)
    c.translate(W/2, H/2); c.rotate(30); c.drawCentredString(0,0,text); c.restoreState()
PY

echo "[3/5] Criando pdf_orcamento_premium.py…"
cat > pdf_orcamento_premium.py <<'PY'
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
PY

echo "[4/5] Injetando rota simples em main.py…"
grep -q "pdf_orcamento_premium" main.py 2>/dev/null || cat >> main.py <<'PY'
# --- rota PDF de Orçamento (premium) ---
from fastapi.responses import FileResponse
from urllib.parse import quote
from pdf_orcamento_premium import gerar_pdf_orcamento_premium

@app.get("/orcamentos/pdf/{orc_id}")
def pdf_orcamento(orc_id: int):
    orc = repo_get_orcamento(orc_id)            # adapte aos seus repos
    os_dados = repo_get_os_dados(orc["os_id"])  # precisa conter os_code, cliente, telefone
    phone = ''.join(ch for ch in os_dados.get('telefone','') if ch.isdigit())
    msg = f"DE ACORDO — {os_dados['os_code']} — ORÇ #{orc_id} — TOTAL {orc['total']:.2f}"
    wa = f"https://wa.me/55{phone}?text={quote(msg)}" if phone else None
    destino = f"/tmp/ORC_{orc_id}_{os_dados['os_code']}.pdf"
    gerar_pdf_orcamento_premium(orc, os_dados, destino, wa_link=wa)
    return FileResponse(destino, media_type="application/pdf", filename=f"ORC_{orc_id}_{os_dados['os_code']}.pdf")
PY

echo "[5/5] Ajustando link do template (se existir)…"
if ls templates/* 1>/dev/null 2>&1; then
  for f in templates/*; do
    grep -q "PDF do orçamento" "$f" 2>/dev/null && \
      sed -i.bak 's#href="[^"]*PDF[^"]*"#href="/orcamentos/pdf/{{ orc.id }}"#g' "$f" || true
  done
fi

echo "Feito! Endpoint: /orcamentos/pdf/<ID>"
