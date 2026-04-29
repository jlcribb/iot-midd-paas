#!/bin/bash
# Script para corregir definitivamente el error de pytest

set -e

echo "🔧 Corrigiendo error de pytest-postgresql..."

# Activar entorno virtual
source venv/bin/activate

# Desinstalar plugins problemáticos (opcionales)
echo "📦 Desinstalando plugins opcionales..."
pip uninstall -y pytest-postgresql pytest-redis psycopg 2>/dev/null || true

# Verificar pytest
echo "🔍 Verificando pytest..."
pytest --version

echo ""
echo "✅ ¡Problema resuelto!"
echo ""
echo "Ahora puedes ejecutar tests:"
echo "  pytest tests/unit/test_messaging/ -v"
echo ""
echo "Si necesitas tests de PostgreSQL en el futuro:"
echo "  pip install -r tests/requirements-test-optional.txt"
