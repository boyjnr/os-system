from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "tiextremo_os.db")

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/os",
    tags=["OS"]
)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/nova", response_class=HTMLResponse)
def os_nova(request: Request):
    return templates.TemplateResponse(
        "os_nova.html",
        {"request": request}
    )

@router.post("/nova", response_class=HTMLResponse)
def os_nova_post(
    request: Request,
    cliente: str = Form(...),
    problema: str = Form(...)
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS os (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            problema TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(
        "INSERT INTO os (cliente, problema) VALUES (?, ?)",
        (cliente, problema)
    )

    conn.commit()
    conn.close()

    return templates.TemplateResponse(
        "os_nova.html",
        {
            "request": request,
            "mensagem": "OS salva com sucesso!"
        }
    )
