import sqlite3, os
from pathlib import Path
db = Path(os.getenv("OS_SQLITE", Path.cwd()/"tiextremo_os.db"))
con = sqlite3.connect(str(db)); cur = con.cursor()
cur.execute("DROP TRIGGER IF EXISTS tr_os_to_orc;")
cur.executescript("""
CREATE TRIGGER tr_os_to_orc
AFTER INSERT ON os
BEGIN
  INSERT OR IGNORE INTO seq_orc(id,valor) VALUES(1,1001);
  INSERT INTO orcamento(os_id,numero,status,cliente_nome,cliente_contato,criado_em)
  VALUES(NEW.id,(SELECT valor FROM seq_orc WHERE id=1),'PENDENTE',NEW.cliente,COALESCE(NEW.telefone,'')||CASE WHEN (COALESCE(NEW.telefone,'')<>'' AND COALESCE(NEW.email,'')<>'') THEN ' / ' ELSE '' END||COALESCE(NEW.email,''),datetime('now'));
  UPDATE seq_orc SET valor=valor+1 WHERE id=1;
END;""")
con.commit(); con.close()
print("OK: trigger instalado no", db)
