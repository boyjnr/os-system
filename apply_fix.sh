#!/bin/bash
set -e
echo "🔧 Aplicando correções no banco tiextremo_crm..."

mysql -u crmuser -pSenhaForte@2025 tiextremo_crm < ~/os-system/fix_schema.sql

echo "✅ Correções aplicadas com sucesso!"
