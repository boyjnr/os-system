#!/bin/bash
set -e

echo ">>> Fazendo backup do serviço..."
cp -a ~/.config/systemd/user/os-system.service ~/.config/systemd/user/os-system.service.bak.$(date +%F-%H%M%S)

echo ">>> Criando override para reduzir memória..."
mkdir -p ~/.config/systemd/user/os-system.service.d

cat > ~/.config/systemd/user/os-system.service.d/override.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/home/servidorland/venv_whatsapp/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8002 --workers 1 --no-access-log --log-level warning
EOF

echo ">>> Recarregando systemd..."
systemctl --user daemon-reload

echo ">>> Reiniciando serviço os-system..."
systemctl --user restart os-system.service

echo ">>> Status resumido:"
systemctl --user status os-system.service --no-pager -l | head -n 20
