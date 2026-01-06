from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pdf_os_premium import gerar_pdf_os_premium

import os, sqlite3, tempfile, time
from datetime import datetime
from typing import Optional, Dict, Any, List

# =========================
# Configurações básicas
# =========================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "tiextremo_os.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="TI Extremo OS System — Staging")
from routers import financeiro
app.include_router(financeiro.router)

# Static & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
@app.get("/os/nova", response_class=HTMLResponse)
def nova_os(request: Request):
    return templates.TemplateResponse("nova_os.html", {"request": request})

# =========================
# Helpers DB
# =========================
NEEDED_COLUMNS = [
    ("status", "TEXT DEFAULT 'Aberta'"),
    ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
    ("os_code", "TEXT"),
    ("analise_tecnica", "TEXT"),
    ("orcamento_json", "TEXT"),
    ("orcamento_subtotal", "REAL DEFAULT 0"),
    ("orcamento_desconto", "REAL DEFAULT 0"),
    ("orcamento_total", "REAL DEFAULT 0"),
    ("orcamento_status", "TEXT DEFAULT ''"),
    ("cep", "TEXT"),
    ("numero", "TEXT"),
]

def db():
    # Conexão resiliente a lock: WAL + busy_timeout
    con = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("PRAGMA busy_timeout=15000;")
        con.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return con

def ensure_columns(con: sqlite3.Connection, table: str, cols: List[tuple]):
    present = {r["name"] for r in con.execute(f"PRAGMA table_info('{table}')")}
    cur = con.cursor()
    for name, decl in cols:
        if name not in present:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    con.commit()

def init_db():
    con = db()
    cur = con.cursor()
    # Tabela OS (mínima)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        endereco TEXT,
        equipamento TEXT,
        modelo TEXT,
        serial TEXT,
        status TEXT DEFAULT 'Aberta',
        problema TEXT NOT NULL,
        anexo TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Garante colunas extras (cep, numero, etc.)
    ensure_columns(con, "os", NEEDED_COLUMNS)

    # Orçamentos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orcamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER NOT NULL,
        data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pendente',
        desconto REAL DEFAULT 0.0,
        observacoes TEXT,
        FOREIGN KEY (os_id) REFERENCES os(id)
    )
    """)
    # Itens do orçamento
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orcamento_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orcamento_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        quantidade INTEGER DEFAULT 1,
        valor_unitario REAL DEFAULT 0.0,
        FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id)
    )
    """)
    con.commit()
    con.close()

init_db()

# =========================
# Funções de domínio
# =========================
def os_code_from(id_: int, created_iso: Optional[str]) -> str:
    try:
        year = datetime.fromisoformat(created_iso).year if created_iso else datetime.now().year
    except Exception:
        year = datetime.now().year
    return f"OS-{year}-{id_:06d}"

def get_or_create_orcamento(con: sqlite3.Connection, os_id: int) -> int:
    row = con.execute("SELECT id FROM orcamentos WHERE os_id = ? LIMIT 1", (os_id,)).fetchone()
    if row:
        return int(row["id"])
    cur = con.cursor()
    cur.execute("INSERT INTO orcamentos (os_id) VALUES (?)", (os_id,))
    con.commit()
    return cur.lastrowid

def load_orcamento(con: sqlite3.Connection, os_id: int) -> Dict[str, Any]:
    # busca/garante orcamento
    orc_id = get_or_create_orcamento(con, os_id)
    itens = con.execute("""
        SELECT id, descricao, quantidade, valor_unitario
        FROM orcamento_itens
        WHERE orcamento_id = ?
        ORDER BY id ASC
    """, (orc_id,)).fetchall()
    itens_py = [dict(x) for x in itens]
    subtotal = 0.0
    for it in itens_py:
        q = float(it.get("quantidade") or 0)
        vu = float(it.get("valor_unitario") or 0.0)
        subtotal += max(0.0, q * vu)
    # desconto pode não existir em algumas bases antigas
    try:
        desc_row = con.execute("SELECT desconto FROM orcamentos WHERE id = ?", (orc_id,)).fetchone()
        desconto = float(desc_row["desconto"] if desc_row and desc_row["desconto"] is not None else 0.0)
    except Exception:
        desconto = 0.0
    total = max(0.0, subtotal - desconto)
    # espelha nos campos da OS se existirem
    try:
        con.execute("""
            UPDATE os SET
                orcamento_subtotal = ?,
                orcamento_desconto = ?,
                orcamento_total = ?
            WHERE id = ?
        """, (subtotal, desconto, total, os_id))
        con.commit()
    except Exception:
        pass
    return {"id": orc_id, "itens": itens_py, "subtotal": subtotal, "desconto": desconto, "total": total}

def retry_exec(cur: sqlite3.Cursor, sql: str, params: tuple, tries: int = 3, delay: float = 0.2):
    for i in range(tries):
        try:
            cur.execute(sql, params)
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and i < tries - 1:
                time.sleep(delay)
                continue
            raise

# =========================
# Rotas
# =========================
@app.get("/health", response_class=PlainTextResponse)
def health():
    return "OK"

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/os/nova", response_class=HTMLResponse)
def os_nova_form(request: Request):
    return templates.TemplateResponse("nova_os.html", {"request": request})

@app.post("/os/nova")
async def os_nova_post(
    cliente: str = Form(...),
    telefone: str = Form(""),
    email: str = Form(""),
    cep: str = Form(""),
    endereco: str = Form(""),
    numero: str = Form(""),
    equipamento: str = Form(""),
    modelo: str = Form(""),
    serial: str = Form(""),
    problema: str = Form(...)
):
    con = db()
    cur = con.cursor()
    try:
        retry_exec(cur, """
            INSERT INTO os (cliente, telefone, email, cep, endereco, numero, equipamento, modelo, serial, problema)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente, telefone, email, cep, endereco, numero, equipamento, modelo, serial, problema))
        con.commit()
        os_id = cur.lastrowid
    finally:
        con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@app.get("/os/listar", response_class=HTMLResponse)
def os_listar(request: Request):
    con = db()
    rows = con.execute("SELECT * FROM os ORDER BY id DESC").fetchall()
    con.close()
    lista = []
    for r in rows:
        d = dict(r)
        d["os_code"] = os_code_from(d["id"], d.get("created_at"))
        lista.append(d)
    return templates.TemplateResponse("listar_os.html", {"request": request, "os_list": lista})

@app.get("/os/ver/{os_id}", response_class=HTMLResponse)
def os_ver(os_id: int, request: Request):
    con = db()
    row = con.execute("SELECT * FROM os WHERE id = ?", (os_id,)).fetchone()
    if not row:
        con.close()
        return HTMLResponse("OS não encontrada.", status_code=404)
    dados = dict(row)
    dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))

    # orçamento
    orc = load_orcamento(con, os_id)
    con.close()

    return templates.TemplateResponse("os_ver.html", {
        "request": request,
        "os": dados,
        "itens": orc["itens"],
        "subtotal": orc["subtotal"],
        "desconto": orc["desconto"],
        "total": orc["total"]
    })

@app.get("/os/editar/{os_id}", response_class=HTMLResponse)
def os_editar_get(os_id: int, request: Request):
    con = db()
    row = con.execute("SELECT * FROM os WHERE id = ?", (os_id,)).fetchone()
    con.close()
    if not row:
        return HTMLResponse("OS não encontrada.", status_code=404)
    dados = dict(row)
    dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))
    return templates.TemplateResponse("os_editar.html", {"request": request, "os": dados})

@app.post("/os/editar/{os_id}")
async def os_editar_post(
    os_id: int,
    cliente: str = Form(...),
    telefone: str = Form(""),
    email: str = Form(""),
    cep: str = Form(""),
    endereco: str = Form(""),
    numero: str = Form(""),
    equipamento: str = Form(""),
    modelo: str = Form(""),
    serial: str = Form(""),
    status_os: str = Form("Aberta"),
    problema: str = Form(...)
):
    con = db()
    cur = con.cursor()
    try:
        retry_exec(cur, """
            UPDATE os SET
                cliente=?, telefone=?, email=?, cep=?, endereco=?, numero=?,
                equipamento=?, modelo=?, serial=?, status=?, problema=?
            WHERE id=?
        """, (cliente, telefone, email, cep, endereco, numero, equipamento, modelo, serial, status_os, problema, os_id))
        con.commit()
    finally:
        con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@app.post("/os/excluir/{os_id}")
async def os_excluir(os_id: int):
    con = db()
    cur = con.cursor()
    try:
        # apaga itens -> orcamento -> os (sem ON DELETE CASCADE garantido)
        orc = con.execute("SELECT id FROM orcamentos WHERE os_id=?", (os_id,)).fetchall()
        for r in orc:
            oid = r["id"]
            cur.execute("DELETE FROM orcamento_itens WHERE orcamento_id=?", (oid,))
        cur.execute("DELETE FROM orcamentos WHERE os_id=?", (os_id,))
        cur.execute("DELETE FROM os WHERE id=?", (os_id,))
        con.commit()
    finally:
        con.close()
    return RedirectResponse(url="/os/listar", status_code=303)

# ---------- Orçamento ----------
@app.post("/orcamento/{os_id}/add_item")
async def orc_add_item(os_id: int,
    descricao: str = Form(...),
    quantidade: int = Form(1),
    valor_unitario: float = Form(0.0)
):
    con = db()
    try:
        orc_id = get_or_create_orcamento(con, os_id)
        cur = con.cursor()
        retry_exec(cur, """
            INSERT INTO orcamento_itens (orcamento_id, descricao, quantidade, valor_unitario)
            VALUES (?, ?, ?, ?)
        """, (orc_id, descricao, int(quantidade or 1), float(valor_unitario or 0.0)))
        con.commit()
    finally:
        con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@app.post("/orcamento/{os_id}/del_item/{item_id}")
async def orc_del_item(os_id: int, item_id: int):
    con = db()
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM orcamento_itens WHERE id=?", (item_id,))
        con.commit()
    finally:
        con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@app.post("/orcamento/{os_id}/desconto")
async def orc_set_desconto(os_id: int, desconto: float = Form(0.0)):
    con = db()
    cur = con.cursor()
    try:
        orc_id = get_or_create_orcamento(con, os_id)
        # garante coluna desconto; se não existir, ignora
        try:
            cur.execute("UPDATE orcamentos SET desconto=? WHERE id=?", (float(desconto or 0.0), orc_id))
        except sqlite3.OperationalError:
            pass
        con.commit()
    finally:
        con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

# ---------- PDF ----------
@app.get("/os/pdf/{os_id}")
def os_pdf(os_id: int):
    con = db()
    row = con.execute("SELECT * FROM os WHERE id = ?", (os_id,)).fetchone()
    if not row:
        con.close()
        return HTMLResponse("OS não encontrada", status_code=404)

    dados = dict(row)
    dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))
    # carrega orçamento para o PDF
    orc = load_orcamento(con, os_id)
    con.close()
    dados["orcamento"] = {
        "itens": orc["itens"],
        "subtotal": orc["subtotal"],
        "desconto": orc["desconto"],
        "total": orc["total"],
    }

    tmpdir = tempfile.mkdtemp(prefix="os_pdf_")
    filename = f"{dados.get('os_code','OS')}.pdf"
    full_path = os.path.join(tmpdir, filename)

    gerar_pdf_os_premium(dados, full_path)

    return FileResponse(full_path, media_type="application/pdf", filename=filename)

# ---------- Dev ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8012)
