from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, sqlite3, tempfile
from datetime import datetime
from typing import Optional
from pdf_os_premium import gerar_pdf_os_premium

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(APP_DIR, "tiextremo_os.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="TI Extremo OS (staging)")
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
