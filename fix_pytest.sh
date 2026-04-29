#!/bin/bash
# Script para corregir el error de pytest-postgresql

set -e

echo "🔧 Corrigiendo error de pytest-postgresql..."

# Activar entorno virtual
source venv/bin/activate

# Instalar psycopg-binary (requerido por pytest-postgresql)
echo "📦 Instalando psycopg-binary..."
pip install psycopg-binary

# Verificar pytest
echo "🔍 Verificando pytest..."
pytest --version

echo ""
echo "✅ ¡Problema resuelto!"
echo ""
echo "Ahora puedes ejecutar tests:"
echo "  pytest tests/unit/test_messaging/ -v"
