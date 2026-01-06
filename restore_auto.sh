#!/bin/bash
set -e

echo ">>> Parando serviço..."
systemctl --user stop os-system.service

echo ">>> Procurando backups main.py.bak.* em ordem reversa..."
BACKUPS=$(ls -1t main.py.bak.*)

for BK in $BACKUPS; do
    echo "--------------------------------------------------"
    echo ">>> Testando backup: $BK"
    cp -a "$BK" main.py

    echo ">>> Reiniciando serviço..."
    systemctl --user daemon-reload
    systemctl --user restart os-system.service
    sleep 3

    STATUS=$(systemctl --user is-active os-system.service || true)
    if [[ "$STATUS" == "active" ]]; then
        echo "✅ Serviço subiu com sucesso usando backup: $BK"
        systemctl --user status os-system.service --no-pager -l | head -n 15
        exit 0
    else
        echo "❌ Falhou com $BK, tentando próximo..."
    fi
done

echo "⚠️ Nenhum backup válido encontrado!"
exit 1
