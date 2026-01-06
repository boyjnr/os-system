import sqlite3, json, sys, os
from datetime import datetime
from pdf_v2 import gerar_pdf_os_v2

DB = os.path.join(os.path.dirname(__file__), "tiextremo_os.db")

def carrega_os(os_id: int):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM os WHERE id=?", (os_id,))
    r = cur.fetchone()
    con.close()
    if not r:
        raise SystemExit(f"OS id {os_id} não encontrada.")
    d = dict(r)
    # tenta montar 'orcamento' a partir das colunas antigas (se existirem)
    orc = {}
    try:
        itens = []
        if d.get("orcamento_json"):
            itens = json.loads(d["orcamento_json"]).get("itens", [])
        orc = {
            "itens": itens or [],
            "subtotal": d.get("orcamento_subtotal") or 0.0,
            "desconto": d.get("orcamento_desconto") or 0.0,
            "total":    d.get("orcamento_total") or 0.0,
        }
    except Exception:
        orc = {"itens": [], "subtotal": 0.0, "desconto": 0.0, "total": 0.0}
    d["orcamento"] = orc
    return d

def main():
    if len(sys.argv) < 2:
        print("uso: python gen_pdf_v2.py <OS_ID> [saida.pdf]")
        raise SystemExit(2)
    os_id = int(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/os_v2_{os_id}.pdf"
    dados = carrega_os(os_id)
    gerar_pdf_os_v2(dados, out)
    print("[OK] Gerado:", out)

if __name__ == "__main__":
    main()
