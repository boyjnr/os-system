#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-/home/servidorland/os-system}"
PY=python3

echo "[1/6] Criando diretórios em $APP_DIR"
mkdir -p "$APP_DIR"


echo "[2/6] Criando venv"
$PY -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"

echo "[3/6] Instalando dependências"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

echo "[4/6] Testando execução local"
cd "$APP_DIR"
$PY - <<'PY'
import sqlite3, os
db=os.path.join(os.environ.get("APP_DIR","/home/servidorland/os-system"),"tiextremo_os.db")
con=sqlite3.connect(db); con.execute("PRAGMA journal_mode=WAL;"); con.close()
print("DB OK:", db)
PY

echo "[5/6] Iniciando com uvicorn (CTRL+C para parar)"
echo "Comando: $APP_DIR/venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8002"
echo "Acesse: http://127.0.0.1:8002"
"$APP_DIR/venv/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8002
