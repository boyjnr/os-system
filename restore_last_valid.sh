#!/usr/bin/env bash
set -euo pipefail
cd ~/os-system

echo "[0] Snapshot do estado atual…"
TS=$(date +%F-%H%M%S)
mkdir -p _snapshot_$TS
cp -a main.py templates pdf_*.py *_orc*.py *_theme*.py 2>/dev/null _snapshot_$TS/ || true
echo "   → Snapshot salvo em: _snapshot_$TS/"

echo "[1] Verificando backups_rapidos…"
[ -d backups_rapidos ] || { echo "ERRO: não existe ~/os-system/backups_rapidos"; exit 1; }

# Restaura main.py se existir no backup
if [ -f backups_rapidos/main.py ]; then
  echo "[2] Restaurando main.py do backup_rapido…"
  cp -a backups_rapidos/main.py main.py
else
  echo "[2] main.py não estava no backup_rapido (OK)."
fi

# Restaura templates se existir cópia
if [ -d backups_rapidos/templates ]; then
  echo "[3] Restaurando templates/ do backup_rapido…"
  rsync -a --delete backups_rapidos/templates/ templates/
else
  echo "[3] backups_rapidos/templates não encontrado (OK)."
fi

# Restaura PDFs se existirem no backup_rapido
restaurados=0
for f in pdf_os_premium.py pdf_orcamento_premium.py; do
  if [ -f "backups_rapidos/$f" ]; then
    cp -a "backups_rapidos/$f" "$f"
    echo "   → restaurado: $f"
    restaurados=$((restaurados+1))
  fi
done
[ $restaurados -eq 0 ] && echo "[4] Nenhum pdf_* no backup_rapido (OK)."

# Opcional: remover arquivos que criamos e podem estar interferindo
echo "[5] Removendo arquivos experimentais (opcional)…"
rm -f pdf_orcamento_match_os.py pdf_theme.py setup_* skin_* patch_* fix_* force_* debug_* 2>/dev/null || true

echo "[6] Reiniciando serviço…"
systemctl --user restart os-system.service || true
echo "Pronto. Faça Ctrl+F5 nas páginas."
