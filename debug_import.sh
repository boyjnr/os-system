#!/bin/bash
set -euo pipefail

echo ">>> Testando import main.py linha por linha..."
SCRIPT="/home/servidorland/os-system/main.py"

lineno=0
while IFS= read -r line; do
    lineno=$((lineno+1))
    echo ">>> Executando linha $lineno: $line"
    # roda só até essa linha
    head -n $lineno "$SCRIPT" > /tmp/test_line.py
    echo -e "\nprint('>>> Linha $lineno OK')" >> /tmp/test_line.py
    if ! python3 /tmp/test_line.py >/tmp/out.log 2>&1; then
        echo ">>> ERRO na linha $lineno"
        cat /tmp/out.log
        exit 1
    fi
done < "$SCRIPT"

echo ">>> Importação linha a linha concluída sem erros."
