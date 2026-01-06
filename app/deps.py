from pathlib import Path
import sqlite3

DB_PATH = Path.home() / "os-system" / "data" / "tiextremo_crm.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
