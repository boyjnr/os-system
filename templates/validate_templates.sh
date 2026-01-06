#!/bin/bash
set -e

cd ~/os-system/templates

echo ">>> Validando templates Jinja em $(pwd)..."
echo

# procura todos .html e tenta compilar
for f in $(find . -type f -name "*.html"); do
    echo ">>> Checando $f"
    python3 - <<PY
import jinja2, sys
from pathlib import Path

file = Path("$f")
src = file.read_text(encoding="utf-8")
env = jinja2.Environment()

try:
    env.parse(src)
    print("   OK ✅")
except Exception as e:
    print("   ERRO ❌ ->", e)
PY
    echo
done
