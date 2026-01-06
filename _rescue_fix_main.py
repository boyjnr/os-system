from pathlib import Path
import re, ast

MAIN = Path("/home/servidorland/os-system/main.py")
s = MAIN.read_text(encoding="utf-8")

# --- normaliza import de responses (tira qualquer coisa extra)
s = re.sub(
    r"^from fastapi\.responses import[^\n]*$",
    "from fastapi.responses import FileResponse, PlainTextResponse",
    s, flags=re.M
)

# --- garante imports necessários
if "from fastapi.responses import FileResponse, PlainTextResponse" not in s:
    s = s.replace(
        "from fastapi import FastAPI, Request",
        "from fastapi import FastAPI, Request\nfrom fastapi.responses import FileResponse, PlainTextResponse"
    )
if "from pdf_orcamento_match_os import gerar_pdf_orcamento_match_os" not in s:
    s = s.replace(
        "from pdf_os_premium import gerar_pdf_os_premium",
        "from pdf_os_premium import gerar_pdf_os_premium\nfrom pdf_orcamento_match_os import gerar_pdf_orcamento_match_os"
    )

# --- remove QUALQUER versão (decorator/def) da rota pdf_orcamento que esteja truncada
s = re.sub(
    r'(?ms)^\s*@app\.get\("/os/\{os_id\}/pdf_orcamento"\)\s*\n', "", s
)
s = re.sub(
    r'(?ms)^\s*def\s+os_pdf_orcamento\([^\)]*\):\s*[\s\S]*?(?=^\s*@app\.|^\s*def\s+|\Z)',
    "",
    s
)

# --- bloco novo, curto e funcional
route_block = '''
@app.get("/os/{os_id}/pdf_orcamento")
def os_pdf_orcamento(os_id: int):
    "Gera o PDF do ORÇAMENTO desta OS (usa campos orcamento_*)."
    import sqlite3, tempfile, os, json
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, os_code, cliente, contato, problema, orcamento_json, orcamento_subtotal, orcamento_desconto, orcamento_total, orcamento_status FROM os WHERE id=?", (os_id,))
    row = cur.fetchone()
    if not row:
        return PlainTextResponse("OS não encontrada", status_code=404)
    os_dados = dict(row)
    os_code = os_dados.get("os_code") or f"OS-{os_id}"
    try:
        itens = (json.loads(os_dados.get("orcamento_json") or "{}") or {}).get("itens", [])
    except Exception:
        itens = []
    if not itens:
        return PlainTextResponse("Sem itens de orçamento para esta OS.", status_code=400)
    orc = {
        "id": os_id,
        "itens": itens,
        "subtotal": float(os_dados.get("orcamento_subtotal") or 0),
        "desconto": float(os_dados.get("orcamento_desconto") or 0),
        "total": float(os_dados.get("orcamento_total") or 0),
        "status": (os_dados.get("orcamento_status") or "").strip() or "PENDENTE",
    }
    tmpdir = tempfile.mkdtemp(prefix="orc_pdf_")
    filename = f"ORC_{os_id}_{os_code}.pdf".replace("/", "-")
    destino = os.path.join(tmpdir, filename)
    gerar_pdf_orcamento_match_os(orc, os_dados, destino, wa_link=None)
    return FileResponse(destino, media_type="application/pdf", filename=filename)
'''

# --- insere no final para não bagunçar âncoras
s = s.rstrip() + "\n" + route_block + "\n"

# --- valida sintaxe
ast.parse(s)

MAIN.write_text(s, encoding="utf-8")
print("OK: main.py saneado e rota /os/{id}/pdf_orcamento instalada.")
