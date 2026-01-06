#!/bin/bash
set -e

FILE="~/os-system/templates/partials/orcamento_inline.html"
BACKUP="~/os-system/templates/partials/orcamento_inline.html.bak.$(date +%Y%m%d-%H%M%S)"

echo ">>> Corrigindo $FILE..."
cp -a $FILE $BACKUP
echo ">>> Backup criado em: $BACKUP"

# Garante que todo bloco {% if %} tem {% endif %}
python3 - <<'PY'
from pathlib import Path

file = Path("/home/servidorland/os-system/templates/partials/orcamento_inline.html")
src = file.read_text(encoding="utf-8").splitlines()

fixed = []
open_ifs = 0

for line in src:
    fixed.append(line)
    if "{% if" in line:
        open_ifs += 1
    if "{% endif" in line:
        open_ifs -= 1

# Se sobrou if aberto, fecha no final
for _ in range(open_ifs):
    fixed.append("{% endif %}")

file.write_text("\n".join(fixed), encoding="utf-8")
print(f">>> Arquivo corrigido: {file}")
PY

echo ">>> Reiniciando serviço os-system..."
systemctl --user restart os-system.service
sleep 2
systemctl --user status os-system.service --no-pager -l | head -n 20
