#!/bin/bash
set -e

ID_OS=${1:-1}  # se não passar parâmetro, usa ID=1

echo ">>> Parando serviço systemd para evitar conflito..."
systemctl --user stop os-system.service || true

echo ">>> Rodando uvicorn em modo DEBUG (porta 8002)..."
echo ">>> Acesse: http://127.0.0.1:8002/os/ver/$ID_OS"
echo ">>> Logs completos abaixo (CTRL+C para parar)..."

exec /home/servidorland/venv_whatsapp/bin/python3 -m uvicorn main:app \
    --host 127.0.0.1 \
    --port 8002 \
    --log-level debug
