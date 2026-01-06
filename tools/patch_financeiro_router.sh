#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/os-system"

MAIN_FILE=""
for p in "$ROOT/main.py" "$ROOT/app/main.py" "$ROOT/src/main.py"; do
  if [ -f "$p" ]; then MAIN_FILE="$p"; break; fi
done

if [ -z "$MAIN_FILE" ]; then
  echo "❌ Não achei main.py em $ROOT/. Me manda o arquivo que eu mando o nano completo."
  exit 1
fi

if grep -q "from routers import financeiro" "$MAIN_FILE"; then
  echo "ℹ️ Router financeiro já presente em: $MAIN_FILE"
  exit 0
fi

cp -a "$MAIN_FILE" "${MAIN_FILE}.bak_$(date +%Y%m%d_%H%M%S)"

awk '
  BEGIN{done=0}
  {
    print $0
    if (!done && $0 ~ /app *= *FastAPI/){
      print "from routers import financeiro"
      print "app.include_router(financeiro.router)"
      done=1
    }
  }
' "$MAIN_FILE" > "${MAIN_FILE}.tmp"

mv "${MAIN_FILE}.tmp" "$MAIN_FILE"
echo "✅ Router financeiro incluído em: $MAIN_FILE"
