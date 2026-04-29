#!/bin/bash

# Script de Instalación de Dependencias para Pruebas - IoT Middleware
# ===================================================================

set -e  # Salir si hay algún error

echo "🧪 Instalando dependencias para pruebas del IoT Middleware..."
echo "=============================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si Python está instalado
check_python() {
    print_status "Verificando instalación de Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION encontrado"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION encontrado"
        PYTHON_CMD="python"
    else
        print_error "Python no está instalado. Por favor instala Python 3.8 o superior."
        exit 1
    fi
    
    # Verificar versión mínima
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Se requiere Python 3.8 o superior. Versión actual: $PYTHON_VERSION"
        exit 1
    fi
}

# Verificar si pip está instalado
check_pip() {
    print_status "Verificando instalación de pip..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        print_success "pip3 encontrado"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        print_success "pip encontrado"
    else
        print_error "pip no está instalado. Por favor instala pip."
        exit 1
    fi
}

# Crear entorno virtual si no existe
create_virtual_env() {
    print_status "Verificando entorno virtual..."
    
    if [ ! -d "venv" ]; then
        print_status "Creando entorno virtual..."
        $PYTHON_CMD -m venv venv
        print_success "Entorno virtual creado"
    else
        print_success "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    print_status "Activando entorno virtual..."
    source venv/bin/activate
    print_success "Entorno virtual activado"
}

# Instalar dependencias base
install_base_dependencies() {
    print_status "Instalando dependencias base..."
    
    # Actualizar pip
    $PIP_CMD install --upgrade pip
    
    # Instalar dependencias del proyecto
    if [ -f "requirements.txt" ]; then
        print_status "Instalando dependencias del proyecto..."
        $PIP_CMD install -r requirements.txt
        print_success "Dependencias del proyecto instaladas"
    else
        print_warning "Archivo requirements.txt no encontrado"
    fi
}

# Instalar dependencias de pruebas
install_test_dependencies() {
    print_status "Instalando dependencias de pruebas..."
    
    if [ -f "tests/requirements-test.txt" ]; then
        $PIP_CMD install -r tests/requirements-test.txt
        print_success "Dependencias de pruebas instaladas"
    else
        print_warning "Archivo tests/requirements-test.txt no encontrado"
        
        # Instalar dependencias básicas de pytest
        print_status "Instalando dependencias básicas de pytest..."
        $PIP_CMD install pytest pytest-cov pytest-mock pytest-asyncio
        print_success "Dependencias básicas de pytest instaladas"
    fi
}

# Verificar instalación
verify_installation() {
    print_status "Verificando instalación..."
    
    # Verificar pytest
    if $PYTHON_CMD -c "import pytest; print('pytest version:', pytest.__version__)" 2>/dev/null; then
        print_success "pytest instalado correctamente"
    else
        print_error "Error al instalar pytest"
        exit 1
    fi
    
    # Verificar pytest-cov
    if $PYTHON_CMD -c "import pytest_cov; print('pytest-cov instalado')" 2>/dev/null; then
        print_success "pytest-cov instalado correctamente"
    else
        print_warning "pytest-cov no está instalado"
    fi
    
    # Verificar pytest-mock
    if $PYTHON_CMD -c "import pytest_mock; print('pytest-mock instalado')" 2>/dev/null; then
        print_success "pytest-mock instalado correctamente"
    else
        print_warning "pytest-mock no está instalado"
    fi
}

# Ejecutar prueba básica
run_basic_test() {
    print_status "Ejecutando prueba básica..."
    
    # Crear archivo de prueba básico si no existe
    if [ ! -f "tests/test_basic.py" ]; then
        cat > tests/test_basic.py << 'EOF'
"""
Prueba básica para verificar que pytest funciona
"""

def test_basic():
    """Prueba básica que siempre pasa"""
    assert True

def test_math():
    """Prueba básica de matemáticas"""
    assert 2 + 2 == 4
    assert 3 * 3 == 9

def test_string():
    """Prueba básica de strings"""
    assert "hello" + " " + "world" == "hello world"
EOF
        print_success "Archivo de prueba básico creado"
    fi
    
    # Ejecutar prueba básica
    if $PYTHON_CMD -m pytest tests/test_basic.py -v; then
        print_success "Prueba básica ejecutada correctamente"
    else
        print_error "Error al ejecutar prueba básica"
        exit 1
    fi
}

# Mostrar información de uso
show_usage_info() {
    echo ""
    echo "🎉 ¡Instalación completada exitosamente!"
    echo "========================================"
    echo ""
    echo "📋 Comandos útiles:"
    echo "  • Activar entorno virtual: source venv/bin/activate"
    echo "  • Ejecutar todas las pruebas: pytest tests/"
    echo "  • Ejecutar pruebas con cobertura: pytest tests/ --cov=src/iot_middleware"
    echo "  • Ejecutar pruebas específicas: pytest tests/unit/test_config/"
    echo "  • Ver ayuda de pytest: pytest --help"
    echo ""
    echo "📁 Estructura de pruebas:"
    echo "  • tests/unit/ - Pruebas unitarias"
    echo "  • tests/integration/ - Pruebas de integración"
    echo "  • tests/performance/ - Pruebas de rendimiento"
    echo "  • tests/security/ - Pruebas de seguridad"
    echo ""
    echo "📚 Documentación:"
    echo "  • README de pruebas: tests/README.md"
    echo "  • Configuración: tests/pytest.ini"
    echo "  • Fixtures: tests/conftest.py"
    echo ""
    echo "🔧 Configuración:"
    echo "  • Archivo de configuración: tests/test_config.yaml"
    echo "  • Variables de entorno: export TEST_ENV=true"
    echo ""
}

# Función principal
main() {
    echo "🧪 Instalador de Dependencias para Pruebas - IoT Middleware"
    echo "============================================================"
    echo ""
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "src/iot_middleware/__init__.py" ]; then
        print_error "Este script debe ejecutarse desde el directorio raíz del proyecto IoT Middleware"
        print_error "Asegúrate de estar en el directorio que contiene src/iot_middleware/"
        exit 1
    fi
    
    # Ejecutar pasos de instalación
    check_python
    check_pip
    create_virtual_env
    install_base_dependencies
    install_test_dependencies
    verify_installation
    run_basic_test
    show_usage_info
    
    print_success "¡Instalación completada exitosamente! 🎉"
}

# Ejecutar función principal
main "$@"
