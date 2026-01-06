from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pdf_os_premium import gerar_pdf_os_premium
import os, sqlite3, tempfile
from datetime import datetime
from typing import Optional

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "tiextremo_os.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="TI Extremo OS System")

app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def os_code_from(id_: int, created_iso: Optional[str]) -> str:
    try:
        year = datetime.fromisoformat(created_iso).year if created_iso else datetime.now().year
    except Exception:
        year = datetime.now().year
    return f"OS-{year}-{id_:06d}"

def init_db():
    con = db(); cur = con.cursor()
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
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        os_code TEXT
    )""")
    con.commit(); con.close()

init_db()

@app.get("/health", response_class=PlainTextResponse)
def health(): return "OK"

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
    endereco: str = Form(""),
    equipamento: str = Form(""),
    modelo: str = Form(""),
    serial: str = Form(""),
    problema: str = Form(...)
):
    con = db(); cur = con.cursor()
    cur.execute("""
        INSERT INTO os (cliente, telefone, email, endereco, equipamento, modelo, serial, problema)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente, telefone, email, endereco, equipamento, modelo, serial, problema))
    con.commit(); os_id = cur.lastrowid; con.close()
    return RedirectResponse(url=f"/os/ver/{os_id}", status_code=303)

@app.get("/os/listar", response_class=HTMLResponse)
def os_listar(request: Request):
    con = db(); cur = con.cursor()
    rows = cur.execute("SELECT * FROM os ORDER BY id DESC").fetchall(); con.close()
    lista = []
    for row in rows:
        dados = dict(row); dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))
        lista.append(dados)
    return templates.TemplateResponse("listar_os.html", {"request": request, "os_list": lista})

@app.get("/os/ver/{os_id}", response_class=HTMLResponse)
def os_ver(os_id: int, request: Request):
    con = db(); row = con.execute("SELECT * FROM os WHERE id = ?", (os_id,)).fetchone(); con.close()
    if not row: return HTMLResponse("OS não encontrada.", status_code=404)
    dados = dict(row); dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))
    return templates.TemplateResponse("os_ver.html", {"request": request, "os": dados})

@app.get("/os/pdf/{os_id}")
def os_pdf(os_id: int):
    con = db(); row = con.execute("SELECT * FROM os WHERE id = ?", (os_id,)).fetchone(); con.close()
    if not row: return HTMLResponse("OS não encontrada", status_code=404)
    dados = dict(row); dados["os_code"] = os_code_from(dados["id"], dados.get("created_at"))
    tmpdir = tempfile.mkdtemp(prefix="os_pdf_")
    filename = f"{dados.get('os_code','OS')}.pdf"; full_path = os.path.join(tmpdir, filename)
    gerar_pdf_os_premium(dados, full_path)
    return FileResponse(full_path, media_type="application/pdf", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
