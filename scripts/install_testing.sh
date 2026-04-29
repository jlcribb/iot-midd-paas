#!/bin/bash
# Script para instalar dependencias de testing

set -e

echo "🧪 Instalando dependencias de testing..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $(python3 --version)${NC}"

# Verificar pip
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip no está disponible${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pip encontrado: $(python3 -m pip --version)${NC}"

# Preguntar si usar entorno virtual
read -p "¿Deseas usar un entorno virtual? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
        python3 -m venv venv
    fi
    
    if [ -d "venv" ]; then
        echo -e "${GREEN}✅ Activando entorno virtual...${NC}"
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo -e "${GREEN}✅ Activando entorno virtual...${NC}"
        source .venv/bin/activate
    fi
fi

# Actualizar pip
echo -e "${YELLOW}📦 Actualizando pip...${NC}"
python3 -m pip install --upgrade pip --quiet

# Instalar dependencias
echo -e "${YELLOW}📦 Instalando dependencias de testing...${NC}"
if python3 -m pip install -r tests/requirements-test.txt; then
    echo -e "${GREEN}✅ Dependencias instaladas exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Intentando con --user...${NC}"
    python3 -m pip install --user -r tests/requirements-test.txt
    echo -e "${GREEN}✅ Dependencias instaladas en modo usuario${NC}"
fi

# Verificar instalación
echo -e "${YELLOW}🔍 Verificando instalación...${NC}"
if python3 -m pytest --version &> /dev/null; then
    echo -e "${GREEN}✅ pytest instalado: $(python3 -m pytest --version)${NC}"
else
    echo -e "${RED}❌ pytest no se pudo verificar${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 ¡Instalación completada!${NC}"
echo ""
echo "Puedes ejecutar tests con:"
echo "  python3 -m pytest tests/unit/test_messaging/ -v"
echo ""
