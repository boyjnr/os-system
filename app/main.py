from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pdf_os_premium import gerar_pdf_os_premium
from routers import financeiro

import os
import sqlite3
import tempfile
import time
from datetime import datetime
from typing import Optional, List

# =========================
# Configurações básicas
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "tiextremo_os.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="TI Extremo OS System — Production")

app.include_router(financeiro.router)

# Static & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# =========================
# Health
# =========================
@app.get("/health", response_class=PlainTextResponse)
def health():
    return "OK"

# =========================
# Home
# =========================
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =========================
# Banco de dados
# =========================
NEEDED_COLUMNS = [
    ("status", "TEXT DEFAULT 'Aberta'"),
    ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
    ("orcamento_subtotal", "REAL DEFAULT 0"),
    ("orcamento_desconto", "REAL DEFAULT 0"),
    ("orcamento_total", "REAL DEFAULT 0"),
    ("cep", "TEXT"),
    ("numero", "TEXT"),
]

def db():
    con = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA busy_timeout=15000;")
    return con

def ensure_columns(con, table: str, cols: List[tuple]):
    present = {r["name"] for r in con.execute(f"PRAGMA table_info('{table}')")}
    cur = con.cursor()
    for name, decl in cols:
        if name not in present:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    con.commit()

def init_db():
    con = db()
    cur = con.cursor()

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_columns(con, "os", NEEDED_COLUMNS)
    con.close()

init_db()

# =========================
# OS — Nova
# =========================
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

    cur.execute("""
        INSERT INTO os (
            cliente, telefone, email, cep, endereco,
            numero, equipamento, modelo, serial, problema
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente, telefone, email, cep, endereco,
        numero, equipamento, modelo, serial, problema
    ))

    con.commit()
    os_id = cur.lastrowid
    con.close()

    return RedirectResponse(url=f"/", status_code=303)
