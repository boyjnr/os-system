import os, sqlite3
from pathlib import Path

db = Path(os.getenv("OS_SQLITE","db.sqlite3"))
db.parent.mkdir(parents=True, exist_ok=True)
db.touch(exist_ok=True)

con = sqlite3.connect(str(db))
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orcamento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  os_id INTEGER,
  numero INTEGER NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'PENDENTE',
  cliente_nome TEXT,
  cliente_contato TEXT,
  validade_dias INTEGER NOT NULL DEFAULT 7,
  desconto_percent REAL NOT NULL DEFAULT 0,
  acrescimos_valor REAL NOT NULL DEFAULT 0,
  observacoes TEXT,
  prazo_execucao TEXT,
  formas_pagto TEXT,
  criado_em TEXT NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orcamento_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  orcamento_id INTEGER NOT NULL,
  descricao TEXT NOT NULL,
  qtd REAL NOT NULL,
  preco REAL NOT NULL,
  FOREIGN KEY(orcamento_id) REFERENCES orcamento(id) ON DELETE CASCADE
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS seq_orc (
  id INTEGER PRIMARY KEY CHECK (id=1),
  valor INTEGER NOT NULL
);
""")

cur.execute("INSERT OR IGNORE INTO seq_orc(id,valor) VALUES(1,1001)")
con.commit()
con.close()
print("OK: esquema de orçamento pronto em", db)
