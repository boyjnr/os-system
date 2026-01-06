#!/usr/bin/env bash
# Migra dados básicos da tabela os de um banco antigo para o novo
set -euo pipefail
OLD_DB="${1:-/home/servidorland/os-system/tiextremo_os.db}"
NEW_DB="${2:-/home/servidorland/os-system/tiextremo_os.db}"
python3 - <<'PY'
import sqlite3, sys
old, new = sys.argv[1], sys.argv[2]
con_old = sqlite3.connect(old); con_old.row_factory=sqlite3.Row
con_new = sqlite3.connect(new); con_new.row_factory=sqlite3.Row
cols = "cliente, telefone, email, endereco, equipamento, modelo, serial, problema, status"
# Assegura tabela no novo DB
con_new.execute("""CREATE TABLE IF NOT EXISTS os (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    telefone TEXT, email TEXT, endereco TEXT,
    equipamento TEXT, modelo TEXT, serial TEXT,
    status TEXT DEFAULT 'Aberta', problema TEXT NOT NULL,
    anexo TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    os_code TEXT
)""")
rows = con_old.execute(f"SELECT {cols} FROM os").fetchall()
for r in rows:
    con_new.execute(f"INSERT INTO os ({cols}) VALUES (?,?,?,?,?,?,?,?,?)", tuple(r[c] for c in cols.split(', ')))
con_new.commit()
print(f"Migradas {len(rows)} OS do banco antigo para o novo.")
PY "$OLD_DB" "$NEW_DB"
