from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import datetime

W, H = A4

def _money(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def _wrap(text, max_w, font="Helvetica", size=9):
    """Quebra o texto respeitando largura e linhas em branco."""
    text = (text or "")
    out = []
    for para in str(text).splitlines() or ["-"]:
        words, cur = para.split(), ""
        for w in words:
            test = (cur + " " + w).strip()
            if stringWidth(test, font, size) <= max_w or not cur:
                cur = test
            else:
                out.append(cur); cur = w
        if cur:
            out.append(cur)
        if para == "" and not out:
            out.append("-")
    return out or ["-"]

def _kv(c, x, y, k, v):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"{(k or '').rstrip(':')}:")
    c.setFont("Helvetica", 9)
    c.drawString(x + 28*mm, y, str(v or "-"))

def gerar_pdf_os_v2(dados, dest_path):
    """
    Gera PDF v2:
    - Cabeçalho minimalista (título + OS + data)
    - Sessões Cliente / Equipamento
    - 'Problema' com altura dinâmica (min 24mm, máx 70mm)
    - Orçamento com tabela paginada e totais SEM invadir rodapé
    """
    m = 18*mm
    y = H - m
    min_footer = 22*mm   # nunca desenhar abaixo disso
    c = canvas.Canvas(dest_path, pagesize=A4)

    def new_page():
        nonlocal y
        c.showPage()
        y = H - m
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#6b7280"))
        c.drawRightString(W - m, H - 10*mm, datetime.now().strftime("%d/%m/%Y %H:%M"))

    # ===== Cabeçalho =====
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W/2, y-6*mm, "T.I. Extremo — Ordem de Serviço")
    y -= 14*mm

    os_code = dados.get("os_code", f"OS-{datetime.now().year}-{dados.get('id',0):06d}")
    created = dados.get("created_at", datetime.now())
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created.replace("Z",""))
        except:
            created = datetime.now()
    data_fmt = created.strftime("%d/%m/%Y %H:%M")

    c.setFont("Helvetica-Bold", 11); c.setFillColor(colors.HexColor("#111827"))
    c.drawCentredString(W/2, y, os_code); y -= 7*mm
    c.setFont("Helvetica", 9.5); c.setFillColor(colors.HexColor("#374151"))
    c.drawCentredString(W/2, y, f"Data: {data_fmt}"); y -= 10*mm

    # ===== Cliente =====
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10.5); c.drawString(m, y, "Dados do Cliente"); y -= 6*mm
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#0f172a"))

    _kv(c, m, y, "Cliente",  dados.get("cliente"));  y -= 5.2*mm
    _kv(c, m, y, "Telefone", dados.get("telefone")); y -= 5.2*mm
    _kv(c, m, y, "E-mail",   dados.get("email"));    y -= 5.2*mm
    _kv(c, m, y, "CEP",      dados.get("cep"));      y -= 5.2*mm

    end_fmt = dados.get("endereco") or "-"
    if dados.get("numero"):
        end_fmt = f"{end_fmt}, {dados.get('numero')}"
    _kv(c, m, y, "Endereço", end_fmt); y -= 8*mm

    # ===== Equipamento =====
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10.5); c.drawString(m, y, "Equipamento"); y -= 6*mm
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#0f172a"))
    _kv(c, m, y, "Tipo",   dados.get("equipamento")); y -= 5.2*mm
    _kv(c, m, y, "Modelo", dados.get("modelo"));      y -= 5.2*mm
    _kv(c, m, y, "Serial/Service Tag", dados.get("serial")); y -= 8*mm

    # ===== Problema (altura dinâmica) =====
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10.5); c.drawString(m, y, "Problema / Sintomas"); y -= 6*mm

    text = (dados.get("problema") or "").strip() or "-"
    max_w = W - 2*m - 6*mm
    lines = _wrap(text, max_w, size=9)
    line_h = 4.2*mm
    box_h = max(24*mm, min(70*mm, len(lines)*line_h + 8*mm))  # 24..70mm

    if y - box_h < min_footer:
        new_page()

    c.setStrokeColor(colors.HexColor("#e5e7eb"))
    c.roundRect(m, y - box_h, W - 2*m, box_h, 4*mm, stroke=1, fill=0)
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#0f172a"))
    ty = y - 5*mm
    for ln in lines:
        if ty < (m + 8*mm): break
        c.drawString(m + 3*mm, ty, ln); ty -= line_h
    y = y - box_h - 8*mm

    # ===== Orçamento (se houver) =====
    orc = dados.get("orcamento") or {}
    itens = orc.get("itens") or []
    if itens:
        def desenha_cabecalho_tabela():
            nonlocal y
            c.setFont("Helvetica-Bold", 10.5)
            c.setFillColor(colors.black)
            c.drawString(m, y, "Orçamento")
            y -= 6*mm
            x_desc = m + 2*mm
            x_qtd  = x_desc + 100*mm
            x_vu   = x_qtd + 22*mm
            x_tot  = x_vu + 28*mm
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_desc, y, "Descrição")
            c.drawString(x_qtd,  y, "Qtd.")
            c.drawString(x_vu,   y, "V. Unit.")
            c.drawString(x_tot,  y, "Total")
            y -= 5*mm
            c.setStrokeColor(colors.HexColor("#e5e7eb")); c.line(m, y, W-m, y); y -= 2*mm
            return x_desc, x_qtd, x_vu, x_tot

        if y < (m + 40*mm):
            new_page()
        x_desc, x_qtd, x_vu, x_tot = desenha_cabecalho_tabela()

        c.setFont("Helvetica", 9)
        for it in itens:
            # quebra a descrição dentro de ~100mm
            desc_lines = _wrap(str(it.get("descricao") or "-"), 100*mm - 4*mm, size=9)
            qtd = int(it.get("quantidade") or 1)
            vu  = float(it.get("valor_unitario") or 0.0)
            tot = qtd * vu

            row_h = max(5*mm, len(desc_lines)*4.2*mm)

            # quebra de página por linha
            if y - row_h < (m + min_footer):
                new_page()
                x_desc, x_qtd, x_vu, x_tot = desenha_cabecalho_tabela()

            # pinta leve a área da linha
            c.setFillColor(colors.HexColor("#f8fafc"))
            c.rect(m, y - row_h + 0.6*mm, W - 2*m, row_h, fill=1, stroke=0)
            c.setFillColor(colors.black)

            ty = y - 4.2*mm
            for dl in desc_lines:
                c.drawString(x_desc, ty, dl); ty -= 4.2*mm

            c.drawRightString(x_qtd + 12*mm, y - 4*mm, str(qtd))
            c.drawRightString(x_vu  + 20*mm, y - 4*mm, _money(vu))
            c.drawRightString(x_tot + 22*mm, y - 4*mm, _money(tot))

            y -= row_h + 1*mm
            c.setStrokeColor(colors.HexColor("#e5e7eb")); c.line(m, y, W-m, y); y -= 1*mm

        # Totais (sempre com espaço)
        if y < (m + 24*mm):
            new_page()
            x_desc, x_qtd, x_vu, x_tot = desenha_cabecalho_tabela()

        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(W - m - 40*mm, y - 2*mm, "Subtotal:")
        c.drawRightString(W - m,          y - 2*mm, _money(orc.get("subtotal", 0.0))); y -= 6*mm

        c.drawRightString(W - m - 40*mm, y - 2*mm, "Desconto:")
        c.drawRightString(W - m,          y - 2*mm, _money(orc.get("desconto", 0.0))); y -= 6*mm

        c.setFont("Helvetica-Bold", 10.5)
        c.drawRightString(W - m - 40*mm, y - 2*mm, "Total:")
        c.drawRightString(W - m,          y - 2*mm, _money(orc.get("total", 0.0))); y -= 10*mm

    # Final
    c.showPage()
    c.save()
