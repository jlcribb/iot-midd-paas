#!/bin/bash
# Script para configurar entorno virtual e instalar dependencias

set -e

echo "🚀 Configurando entorno virtual..."

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $(python3 --version)${NC}"

# Eliminar venv existente si hay problemas
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Eliminando entorno virtual existente...${NC}"
    rm -rf venv
fi

# Crear entorno virtual
echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
python3 -m venv venv

# Activar entorno virtual
echo -e "${GREEN}✅ Activando entorno virtual...${NC}"
source venv/bin/activate

# Actualizar pip
echo -e "${YELLOW}📦 Actualizando pip...${NC}"
pip install --upgrade pip --quiet

# Instalar dependencias principales
echo -e "${YELLOW}📦 Instalando dependencias principales...${NC}"
pip install -r requirements.txt

# Instalar dependencias de testing
echo -e "${YELLOW}📦 Instalando dependencias de testing...${NC}"
pip install -r tests/requirements-test.txt

# Verificar instalación
echo -e "${YELLOW}🔍 Verificando instalación...${NC}"
if pytest --version &> /dev/null; then
    echo -e "${GREEN}✅ pytest instalado: $(pytest --version)${NC}"
else
    echo -e "${RED}❌ pytest no se pudo verificar${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 ¡Instalación completada exitosamente!${NC}"
echo ""
echo "Para usar el entorno virtual:"
echo "  source venv/bin/activate"
echo ""
echo "Para ejecutar tests:"
echo "  pytest tests/unit/test_messaging/ -v"
echo ""
