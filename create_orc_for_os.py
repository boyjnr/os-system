import os,sqlite3,sys
from pathlib import Path
if len(sys.argv)!=2: print("uso: python3 create_orc_for_os.py <os_id>"); exit(1)
os_id=int(sys.argv[1])
db=Path(os.getenv("OS_SQLITE", Path.cwd()/ "tiextremo_os.db"))
con=sqlite3.connect(str(db)); cur=con.cursor()
cur.execute("INSERT INTO orcamento(os_id,status,created_at) VALUES(?,?,datetime('now'))",
            (os_id,"PENDENTE"))
con.commit(); con.close()
print(f"OK: orcamento pendente criado p/ OS {os_id}")
