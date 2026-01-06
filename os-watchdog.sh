#!/bin/bash

PORT=8001

while true; do
  # Pega o PID que está na 8001
  PID=$(lsof -ti tcp:$PORT)

  if [ -n "$PID" ]; then
    # Descobre se é do systemd
    OWNER=$(ps -o cmd= -p $PID)

    if [[ "$OWNER" != *"uvicorn main:app --host 0.0.0.0 --port 8001"* ]]; then
      echo ">>> Watchdog: processo estranho na porta $PORT ($OWNER). Matando PID $PID..."
      kill -9 $PID
      systemctl --user restart os-system.service
    fi
  fi

  sleep 15
done
