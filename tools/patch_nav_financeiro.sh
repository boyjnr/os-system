#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/os-system"
# candidatos comuns de layout
CANDS=(
  "$ROOT/templates/base.html"
  "$ROOT/templates/layout.html"
  "$ROOT/templates/_navbar.html"
  "$ROOT/app/templates/base.html"
  "$ROOT/app/templates/layout.html"
  "$ROOT/app/templates/_navbar.html"
)

TARGET=""
for f in "${CANDS[@]}"; do
  if [[ -f "$f" ]] && grep -q "Listar OS" "$f"; then
    TARGET="$f"; break
  fi
done

if [[ -z "$TARGET" ]]; then
  echo "❌ Não achei layout com 'Listar OS'. Me manda o arquivo que eu faço o nano completo."
  exit 1
fi

cp -a "$TARGET" "${TARGET}.bak_$(date +%Y%m%d_%H%M%S)"

# Se já houver Financeiro, saímos
if grep -q '/financeiro/listar' "$TARGET"; then
  echo "ℹ️ Link Financeiro já existe em: $TARGET"
  exit 0
fi

# tenta inserir após 'Nova OS' (ou após 'Listar OS' se não tiver Nova OS)
if grep -q "Nova OS" "$TARGET"; then
  awk '
    BEGIN{done=0}
    {
      print $0
      if (!done && $0 ~ /Nova OS/){
        print "            <li><a href=\"/financeiro/listar\">Financeiro</a></li>"
        done=1
      }
    }
  ' "$TARGET" > "${TARGET}.tmp"
else
  awk '
    BEGIN{done=0}
    {
      print $0
      if (!done && $0 ~ /Listar OS/){
        print "            <li><a href=\"/financeiro/listar\">Financeiro</a></li>"
        done=1
      }
    }
  ' "$TARGET" > "${TARGET}.tmp"
fi

mv "${TARGET}.tmp" "$TARGET"
echo "✅ Link 'Financeiro' adicionado em: $TARGET"
