import sys, sqlite3, os
from pathlib import Path
db = Path(os.getenv("OS_SQLITE","db.sqlite3"))
if len(sys.argv)!=2:
    print("uso: python3 set_next_os_sqlite.py 2378"); sys.exit(1)
nextv=int(sys.argv[1])
if not db.exists():
    print(f"arquivo SQLite não encontrado: {db}"); sys.exit(2)
con=sqlite3.connect(str(db))
cur=con.cursor()
try:
    cur.execute("UPDATE seq_os SET valor=?",(nextv,))
    con.commit()
    print(f"OK: sequência atualizada para {nextv}")
except sqlite3.Error as e:
    print("Falha ao atualizar seq_os:", e)
finally:
    con.close()
