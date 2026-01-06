#!/bin/bash
set -e

TARGET="$HOME/os-system/main.py"
BACKUP="$TARGET.bak.$(date +%F-%H%M%S)"

echo ">>> Backup em: $BACKUP"
cp -a "$TARGET" "$BACKUP"

# Garante que app = FastAPI() existe antes de qualquer @app.route
awk '
BEGIN { fixed=0 }
/^from fastapi/ {
    print
    next
}
/^app = FastAPI\(\)/ { found=1 }
{ print }
END {
    if (!found) {
        print ""
        print "from fastapi import FastAPI"
        print "app = FastAPI()"
    }
}' "$BACKUP" > "$TARGET"

echo ">>> Corrigido main.py (app garantido no topo)"
systemctl --user restart os-system.service
sleep 2
systemctl --user status os-system.service --no-pager -l | head -n 20
