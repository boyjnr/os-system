#!/bin/bash
set -e

cd ~/os-system

echo ">>> Parando serviço..."
systemctl --user stop os-system.service || true

# Lista candidatos (ordem decrescente por data, escolhe manual ou automático)
echo ">>> Últimos backups disponíveis:"
ls -lh main.py.bak.2025-09-24* main.py.bak.2025-09-25* | tail -n 10

# Escolhe um estável (ajuste se quiser outro)
CANDIDATE="main.py.bak.2025-09-25-173257"

echo ">>> Restaurando backup estável: $CANDIDATE"
cp -a "$CANDIDATE" main.py

echo ">>> Recarregando systemd..."
systemctl --user daemon-reexec

echo ">>> Reiniciando serviço os-system..."
systemctl --user restart os-system.service

sleep 2
systemctl --user status os-system.service --no-pager -l | head -n 20
