from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from datetime import datetime, timedelta

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])
DB = "/home/servidorland/os-system/tiextremo_crm.sqlite"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def periodo_range(periodo: str):
    hoje = datetime.now()
    if periodo == "este_mes":
        ini = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prox = (ini.replace(day=28) + timedelta(days=4)).replace(day=1)
        fim = prox
    elif periodo == "mes_passado":
        fim = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ini = (fim.replace(day=1) - timedelta(days=1)).replace(day=1)
    elif periodo == "ult_30":
        ini = hoje - timedelta(days=30)
        fim = hoje + timedelta(days=1)
    else:
        ini = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fim = hoje + timedelta(days=1)
    return ini, fim

@router.get("/listar", response_class=HTMLResponse)
def listar(request: Request, status: str = "a_receber", periodo: str = "este_mes", os_id: int | None = None):
    ini, fim = periodo_range(periodo)
    q = """
    SELECT id, os_id, cliente_nome, descricao, valor_liquido, forma_pagto, status, vencimento, emitido_em
    FROM financeiro_lancamentos
    WHERE status = ?
      AND emitido_em BETWEEN ? AND ?
    """
    params = [status, ini.isoformat(" "), fim.isoformat(" ")]
    if os_id:
        q += " AND os_id = ?"
        params.append(os_id)
    q += " ORDER BY id DESC"

    con = db(); cur = con.cursor()
    rows = cur.execute(q, params).fetchall()
    total = sum([(r["valor_liquido"] or 0) for r in rows])

    def tr(r):
        return f"""
        <tr>
          <td>{r['id']}</td>
          <td><a href="/os/abrir/{r['os_id']}">OS {r['os_id']}</a></td>
          <td>{r['cliente_nome'] or ''}</td>
          <td style="text-align:right">R$ { (r['valor_liquido'] or 0):,.2f}</td>
          <td>{r['forma_pagto'] or ''}</td>
          <td><span class="badge bg-secondary">{r['status']}</span></td>
          <td>{r['vencimento'] or ''}</td>
          <td>
            <a class="btn btn-sm btn-success" href="/financeiro/receber?id={r['id']}">Receber</a>
          </td>
        </tr>"""

    html = f"""
    <div class="container mt-3">
      <h3>Financeiro — {status.replace('_',' ').title()}</h3>
      <div class="mb-2">
        <a class="btn btn-sm btn-outline-primary" href="/financeiro/listar?status=a_receber">A receber</a>
        <a class="btn btn-sm btn-outline-success" href="/financeiro/listar?status=recebido">Recebido</a>
        <a class="btn btn-sm btn-outline-secondary" href="/financeiro/listar?status=cancelado">Cancelado</a>
      </div>
      <table class="table table-striped align-middle">
        <thead>
          <tr>
            <th>#</th><th>OS</th><th>Cliente</th>
            <th style="text-align:right">Valor (R$)</th>
            <th>Forma</th><th>Status</th><th>Vencimento</th><th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {''.join([tr(r) for r in rows])}
        </tbody>
        <tfoot>
          <tr>
            <th colspan="3" style="text-align:right">Total:</th>
            <th style="text-align:right">R$ {total:,.2f}</th>
            <th colspan="4"></th>
          </tr>
        </tfoot>
      </table>
    </div>
    """
    con.close()
    return HTMLResponse(html)

@router.get("/gerar")
def gerar(os_id: int, orcamento_id: int):
    con = db(); cur = con.cursor()

    o = cur.execute("""
      SELECT valor_total, COALESCE(forma_pagto,'PIX') as forma, COALESCE(parcelas,1) as parcelas, COALESCE(entrada_valor,0) as entrada
      FROM orcamentos WHERE id=? AND os_id=? AND status='aprovado'
    """, (orcamento_id, os_id)).fetchone()
    if not o:
        con.close()
        raise HTTPException(400, "Orçamento não aprovado (ou inexistente).")

    valor = float(o["valor_total"]); forma = o["forma"]; parcelas = int(o["parcelas"]); entrada = float(o["entrada"])

    os_row = cur.execute("SELECT cliente_nome FROM os WHERE id=?", (os_id,)).fetchone()
    cliente = os_row["cliente_nome"] if os_row else ""
    desc = f"Lançamento OS {os_id} — orçamento {orcamento_id}"

    cur.execute("""
      INSERT INTO financeiro_lancamentos (os_id, cliente_nome, descricao, valor_bruto, desconto, acrescimo, valor_liquido, forma_pagto, status, emitido_em)
      VALUES (?, ?, ?, ?, 0, 0, ?, ?, 'a_receber', datetime('now'))
    """, (os_id, cliente, desc, valor, valor, forma))
    lanc_id = cur.lastrowid

    if parcelas <= 1:
        cur.execute("""
          INSERT INTO financeiro_parcelas (lancamento_id, parcela_num, valor, vencimento, status)
          VALUES (?, 1, ?, date('now','+3 day'), 'a_receber')
        """, (lanc_id, valor))
    else:
        restante = valor
        if entrada > 0:
            cur.execute("""
              INSERT INTO financeiro_parcelas (lancamento_id, parcela_num, valor, vencimento, status)
              VALUES (?, 0, ?, date('now'), 'a_receber')
            """, (lanc_id, entrada))
            restante = max(valor - entrada, 0)
        parcela_val = round(restante / parcelas, 2)
        for i in range(1, parcelas+1):
            cur.execute("""
              INSERT INTO financeiro_parcelas (lancamento_id, parcela_num, valor, vencimento, status)
              VALUES (?, ?, ?, date('now', ? || ' month'), 'a_receber')
            """, (lanc_id, i, parcela_val, str(i)))

    con.commit(); con.close()
    return RedirectResponse(url=f"/financeiro/listar?os_id={os_id}", status_code=302)

@router.get("/receber")
def receber(id: int):
    con = db(); cur = con.cursor()
    cur.execute("""
      UPDATE financeiro_lancamentos
      SET status='recebido', recebido_em=datetime('now')
      WHERE id=?
    """, (id,))
    cur.execute("""
      UPDATE financeiro_parcelas
      SET status='recebido', pago_em=datetime('now')
      WHERE lancamento_id=? AND status='a_receber'
    """, (id,))
    con.commit(); con.close()
    return RedirectResponse(url="/financeiro/listar?status=recebido", status_code=302)

@router.get("/aprovar_orcamento")
def aprovar_orcamento(orcamento_id: int, os_id: int, forma_pagto: str = "PIX", parcelas: int = 1, entrada_valor: float = 0.0, aprovado_por: str = "admin"):
    con = db(); cur = con.cursor()
    cur.execute("""
      UPDATE orcamentos
      SET status='aprovado', aprovado_por=?, aprovado_em=datetime('now'),
          forma_pagto=?, parcelas=?, entrada_valor=?
      WHERE id=? AND os_id=?
    """, (aprovado_por, forma_pagto, parcelas, entrada_valor, orcamento_id, os_id))
    if cur.rowcount == 0:
        con.close()
        raise HTTPException(400, "Orçamento não encontrado.")
    con.commit(); con.close()
    return RedirectResponse(url=f"/financeiro/gerar?os_id={os_id}&orcamento_id={orcamento_id}", status_code=302)
