#!/bin/bash

# Script de Instalación de Dependencias - Sistema de Demostración IoT Middleware
# =============================================================================

set -e  # Salir en caso de error

echo "🚀 Instalando dependencias para el Sistema de Demostración IoT Middleware"
echo "=================================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con colores
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
        PYTHON_CMD="python3"
        print_success "Python 3 encontrado: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        print_success "Python encontrado: $(python --version)"
    else
        print_error "Python no está instalado. Por favor instala Python 3.7+"
        exit 1
    fi
}

# Verificar si pip está instalado
check_pip() {
    print_status "Verificando instalación de pip..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        print_success "pip3 encontrado: $(pip3 --version)"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        print_success "pip encontrado: $(pip --version)"
    else
        print_error "pip no está instalado. Por favor instala pip"
        exit 1
    fi
}

# Instalar dependencias básicas
install_basic_dependencies() {
    print_status "Instalando dependencias básicas..."
    
    # Dependencias esenciales para la demostración
    local basic_deps=(
        "matplotlib"
        "numpy"
        "pyyaml"
        "requests"
    )
    
    for dep in "${basic_deps[@]}"; do
        print_status "Instalando $dep..."
        if $PIP_CMD install --user "$dep" > /dev/null 2>&1; then
            print_success "$dep instalado correctamente"
        else
            print_warning "Error instalando $dep, intentando con --user..."
            $PIP_CMD install --user "$dep"
        fi
    done
}

# Instalar dependencias opcionales para persistencia
install_optional_dependencies() {
    print_status "Instalando dependencias opcionales para persistencia..."
    
    # Dependencias para PostgreSQL
    local postgresql_deps=(
        "sqlalchemy"
        "psycopg2-binary"
    )
    
    # Dependencias para InfluxDB
    local influxdb_deps=(
        "influxdb-client"
    )
    
    # Dependencias para MIDI
    local midi_deps=(
        "mido"
        "python-rtmidi"
    )
    
    # Dependencias para Modbus
    local modbus_deps=(
        "pymodbus"
    )
    
    print_status "Dependencias PostgreSQL (opcional):"
    for dep in "${postgresql_deps[@]}"; do
        if $PIP_CMD install --user "$dep" > /dev/null 2>&1; then
            print_success "$dep instalado"
        else
            print_warning "$dep no se pudo instalar (opcional)"
        fi
    done
    
    print_status "Dependencias InfluxDB (opcional):"
    for dep in "${postgresql_deps[@]}"; do
        if $PIP_CMD install --user "$dep" > /dev/null 2>&1; then
            print_success "$dep instalado"
        else
            print_warning "$dep no se pudo instalar (opcional)"
        fi
    done
    
    print_status "Dependencias MIDI (opcional):"
    for dep in "${midi_deps[@]}"; do
        if $PIP_CMD install --user "$dep" > /dev/null 2>&1; then
            print_success "$dep instalado"
        else
            print_warning "$dep no se pudo instalar (opcional)"
        fi
    done
    
    print_status "Dependencias Modbus (opcional):"
    for dep in "${modbus_deps[@]}"; do
        if $PIP_CMD install --user "$dep" > /dev/null 2>&1; then
            print_success "$dep instalado"
        else
            print_warning "$dep no se pudo instalar (opcional)"
        fi
    done
}

# Verificar instalación
verify_installation() {
    print_status "Verificando instalación..."
    
    # Verificar dependencias básicas
    local basic_deps=("matplotlib" "numpy" "pyyaml")
    local missing_basic=()
    
    for dep in "${basic_deps[@]}"; do
        if ! $PYTHON_CMD -c "import $dep" 2>/dev/null; then
            missing_basic+=("$dep")
        fi
    done
    
    if [ ${#missing_basic[@]} -eq 0 ]; then
        print_success "Todas las dependencias básicas están instaladas"
    else
        print_error "Faltan dependencias básicas: ${missing_basic[*]}"
        return 1
    fi
    
    # Verificar dependencias opcionales
    local optional_deps=("sqlalchemy" "psycopg2" "influxdb_client" "mido" "pymodbus")
    local installed_optional=()
    
    for dep in "${optional_deps[@]}"; do
        if $PYTHON_CMD -c "import $dep" 2>/dev/null; then
            installed_optional+=("$dep")
        fi
    done
    
    if [ ${#installed_optional[@]} -gt 0 ]; then
        print_success "Dependencias opcionales instaladas: ${installed_optional[*]}"
    else
        print_warning "No se instalaron dependencias opcionales"
    fi
    
    return 0
}

# Crear directorios necesarios
create_directories() {
    print_status "Creando directorios necesarios..."
    
    local dirs=(
        "demo_outputs"
        "demo_outputs/reports"
        "demo_outputs/charts"
        "demo_outputs/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Directorio creado: $dir"
        else
            print_status "Directorio ya existe: $dir"
        fi
    done
}

# Mostrar información de uso
show_usage_info() {
    echo ""
    echo "🎉 Instalación completada exitosamente!"
    echo "=================================================================="
    echo ""
    echo "📁 Directorios creados:"
    echo "  - demo_outputs/          # Directorio principal de salida"
    echo "  - demo_outputs/reports/  # Informes generados"
    echo "  - demo_outputs/charts/   # Gráficos y visualizaciones"
    echo "  - demo_outputs/logs/     # Logs de demostración"
    echo ""
    echo "🚀 Para ejecutar una demostración:"
    echo "  cd examples"
    echo "  python demo_rapida.py     # Demostración rápida (3-5 min)"
    echo "  python demo_completa.py   # Demostración completa"
    echo ""
    echo "📚 Documentación:"
    echo "  - docs/legacy/README_DEMOSTRACION.md  # Guía completa de demostración"
    echo "  - docs/legacy/README_MULTI_PROTOCOL.md # Arquitectura multi-protocolo"
    echo ""
    echo "🔧 Dependencias instaladas:"
    echo "  ✅ Básicas: matplotlib, numpy, pyyaml, requests"
    echo "  🔶 Opcionales: sqlalchemy, psycopg2, influxdb-client, mido, pymodbus"
    echo ""
}

# Función principal
main() {
    echo "🚀 Sistema de Demostración IoT Middleware"
    echo "=========================================="
    echo ""
    
    # Verificar requisitos previos
    check_python
    check_pip
    
    echo ""
    
    # Instalar dependencias
    install_basic_dependencies
    echo ""
    install_optional_dependencies
    echo ""
    
    # Verificar instalación
    if verify_installation; then
        print_success "Instalación verificada correctamente"
    else
        print_error "Error en la verificación de instalación"
        exit 1
    fi
    
    echo ""
    
    # Crear directorios
    create_directories
    
    echo ""
    
    # Mostrar información de uso
    show_usage_info
}

# Ejecutar función principal
main "$@"
