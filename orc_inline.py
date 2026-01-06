from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import json, sqlite3, os

router = APIRouter()

def resolve_db_connection():
    """
    Usa a conexão oficial do projeto se existir (main.get_db_connection),
    senão cai no SQLite local tiextremo_os.db (somente leitura/escrita simples).
    """
    try:
        from main import get_db_connection
        return get_db_connection()
    except Exception:
        db = os.path.expanduser("~/os-system/tiextremo_os.db")
        return sqlite3.connect(db)

def _detect_os_table(cur):
    for t in ("os", "ordens_servico"):
        try:
            cur.execute(f"SELECT 1 FROM {t} LIMIT 1")
            return t
        except Exception:
            continue
    return None

def _parse_form_items(form):
    """
    Aceita formatos:
      itens[0][descricao], itens[0][qtd], itens[0][unit] (recomendado)
    ou itens[][descricao] / descricao[] / qtd[] / unit[] (fallback)
    """
    items = {}
    # 1) indexado: itens[<i>][campo]
    for k, v in form.multi_items():
        if k.startswith("itens[") and "][" in k:
            # itens[3][descricao]
            try:
                idx = int(k.split("[",1)[1].split("]",1)[0])
                campo = k.split("][",1)[1].split("]",1)[0]
            except Exception:
                continue
            items.setdefault(idx, {})[campo] = v

    if items:
        out = []
        for i in sorted(items.keys()):
            d = items[i].get("descricao","").strip()
            q = float(str(items[i].get("qtd","0")).replace(",", ".") or 0)
            u = float(str(items[i].get("unit","0")).replace(",", ".") or 0)
            out.append({"descricao": d, "qtd": q, "unit": u})
        return out

    # 2) fallback por listas paralelas
    descs = form.getlist("itens[][descricao]") or form.getlist("descricao[]") or []
    qtds  = form.getlist("itens[][qtd]")       or form.getlist("qtd[]")       or []
    units = form.getlist("itens[][unit]")      or form.getlist("unit[]")      or []
    n = max(len(descs), len(qtds), len(units))
    out = []
    for i in range(n):
        d = (descs[i] if i<len(descs) else "").strip()
        q = float(str(qtds[i] if i<len(qtds) else "0").replace(",", ".") or 0)
        u = float(str(units[i] if i<len(units) else "0").replace(",", ".") or 0)
        out.append({"descricao": d, "qtd": q, "unit": u})
    return out

@router.post("/os/{os_id}/orcamento/salvar")
async def salvar_orcamento(os_id: int, request: Request):
    form = await request.form()
    itens = _parse_form_items(form)
    desconto = float(str(form.get("desconto","0")).replace(",", ".") or 0)

    subtotal = sum((it["qtd"] or 0) * (it["unit"] or 0) for it in itens)
    total = max(subtotal - desconto, 0)

    conn = resolve_db_connection()
    cur = conn.cursor()
    tbl = _detect_os_table(cur)
    if not tbl:
        return JSONResponse({"detail":"Tabela de OS não encontrada"}, status_code=500)

    cur.execute(f"""UPDATE {tbl}
                    SET orcamento_json=?,
                        orcamento_subtotal=?,
                        orcamento_desconto=?,
                        orcamento_total=?,
                        orcamento_status=?
                  WHERE id=?""",
                (json.dumps(itens, ensure_ascii=False),
                 float(subtotal), float(desconto), float(total),
                 "PENDENTE", os_id))
    conn.commit()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@router.get("/os/{os_id}/orcamento/json")
def get_orcamento_json(os_id: int):
    conn = resolve_db_connection()
    cur = conn.cursor()
    tbl = _detect_os_table(cur)
    if not tbl:
        return {"itens": [], "subtotal": 0, "desconto": 0, "total": 0, "status": ""}

    try:
        cur.execute(f"""SELECT orcamento_json, orcamento_subtotal,
                               orcamento_desconto, orcamento_total, orcamento_status
                        FROM {tbl} WHERE id=?""", (os_id,))
        row = cur.fetchone()
    except Exception:
        row = None

    if not row:
        return {"itens": [], "subtotal": 0, "desconto": 0, "total": 0, "status": ""}

    oj, sb, ds, tt, st = row
    try:
        itens = json.loads(oj) if oj else []
    except Exception:
        itens = []
    return {"itens": itens, "subtotal": sb or 0, "desconto": ds or 0, "total": tt or 0, "status": st or ""}

# --- compat: main.py importa isso no startup; deixamos como no-op seguro ---
async def bootstrap_orc_inline():
    return None

@router.get("/os/{os_id}/enviar_aprovacao")
def orc_enviar_aprovacao(os_id: int):
    """Atualiza orcamento_status e volta para /os/ver/{id}."""
    import sqlite3
    conn = resolve_db_connection()
    cur = conn.cursor()
    # detecta tabela
    tbl = None
    for t in ("os", "ordens_servico"):
        try:
            cur.execute(f"SELECT id FROM {t} WHERE id=?", (os_id,))
            if cur.fetchone():
                tbl = t; break
        except Exception:
            pass
    if not tbl:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    cur.execute(f"UPDATE {tbl} SET orcamento_status=? WHERE id=?", ("AGUARDANDO_CLIENTE", os_id))
    conn.commit()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@router.get("/os/{os_id}/aprovar")
def orc_aprovar(os_id: int):
    """Atualiza orcamento_status e volta para /os/ver/{id}."""
    import sqlite3
    conn = resolve_db_connection()
    cur = conn.cursor()
    # detecta tabela
    tbl = None
    for t in ("os", "ordens_servico"):
        try:
            cur.execute(f"SELECT id FROM {t} WHERE id=?", (os_id,))
            if cur.fetchone():
                tbl = t; break
        except Exception:
            pass
    if not tbl:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    cur.execute(f"UPDATE {tbl} SET orcamento_status=? WHERE id=?", ("APROVADO", os_id))
    conn.commit()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@router.get("/os/{os_id}/reprovar")
def orc_reprovar(os_id: int):
    """Atualiza orcamento_status e volta para /os/ver/{id}."""
    import sqlite3
    conn = resolve_db_connection()
    cur = conn.cursor()
    # detecta tabela
    tbl = None
    for t in ("os", "ordens_servico"):
        try:
            cur.execute(f"SELECT id FROM {t} WHERE id=?", (os_id,))
            if cur.fetchone():
                tbl = t; break
        except Exception:
            pass
    if not tbl:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    cur.execute(f"UPDATE {tbl} SET orcamento_status=? WHERE id=?", ("REPROVADO", os_id))
    conn.commit()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)
