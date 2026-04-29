#!/bin/bash
# Script de inicio para el Dashboard de Monitoreo

set -e

echo "🚀 Iniciando Dashboard de Monitoreo..."

# Verificar que Python esté instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

# Verificar que las dependencias estén instaladas
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -q -r requirements.txt

# Verificar variables de entorno
if [ -z "$RABBITMQ_HOST" ]; then
    export RABBITMQ_HOST=${RABBITMQ_HOST:-localhost}
    echo "⚠️  RABBITMQ_HOST no configurado, usando: $RABBITMQ_HOST"
fi

if [ -z "$DASHBOARD_PORT" ]; then
    export DASHBOARD_PORT=${DASHBOARD_PORT:-8080}
    echo "⚠️  DASHBOARD_PORT no configurado, usando: $DASHBOARD_PORT"
fi

# Iniciar dashboard
echo "✅ Iniciando dashboard en http://localhost:$DASHBOARD_PORT"
echo "📊 Accede al dashboard en: http://localhost:$DASHBOARD_PORT"
echo ""

python -m containers.dashboard.main
