import sqlite3, os
from pathlib import Path
db = Path(os.getenv("OS_SQLITE","db.sqlite3"))
if not db.exists():
    # seu projeto usa tiextremo_os.db; se for o caso, tenta esse
    db = Path(os.getenv("DB_PATH", Path(__file__).parent / "tiextremo_os.db"))
con = sqlite3.connect(str(db))
cur = con.cursor()

# remove trigger antigo (se existir)
cur.execute("DROP TRIGGER IF EXISTS tr_os_to_orc;")

# cria trigger: quando inserir em OS, cria orçamento pendente e incrementa seq_orc
cur.executescript("""
CREATE TRIGGER tr_os_to_orc
AFTER INSERT ON os
BEGIN
  INSERT OR IGNORE INTO seq_orc(id,valor) VALUES(1,1001);

  INSERT INTO orcamento
    (os_id, numero, status, cliente_nome, cliente_contato, criado_em)
  VALUES
    (
      NEW.id,
      (SELECT valor FROM seq_orc WHERE id=1),
      'PENDENTE',
      NEW.cliente,
      TRIM(
        COALESCE(NEW.telefone,'') ||
        CASE WHEN (COALESCE(NEW.telefone,'')<>'' AND COALESCE(NEW.email,'')<>'') THEN ' / ' ELSE '' END ||
        COALESCE(NEW.email,'')
      ),
      datetime('now')
    );

  UPDATE seq_orc SET valor = valor + 1 WHERE id=1;
END;
""")

con.commit()
con.close()
print("OK: trigger tr_os_to_orc instalado")
