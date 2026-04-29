#!/bin/bash

# Script de Ejecución de Pruebas - IoT Middleware
# ===============================================

set -e  # Salir si hay algún error

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

# Función para mostrar ayuda
show_help() {
    echo "🧪 Script de Ejecución de Pruebas - IoT Middleware"
    echo "=================================================="
    echo ""
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help              Mostrar esta ayuda"
    echo "  -u, --unit              Ejecutar solo pruebas unitarias"
    echo "  -i, --integration       Ejecutar solo pruebas de integración"
    echo "  -p, --performance       Ejecutar solo pruebas de rendimiento"
    echo "  -s, --security          Ejecutar solo pruebas de seguridad"
    echo "  -c, --coverage          Ejecutar pruebas con cobertura"
    echo "  -r, --report            Generar reportes HTML"
    echo "  -d, --docker            Ejecutar pruebas en Docker"
    echo "  -v, --verbose           Output verbose"
    echo "  -f, --failed            Solo pruebas que fallaron"
    echo "  --slow                  Solo pruebas lentas"
    echo "  --fast                  Solo pruebas rápidas"
    echo "  --clean                 Limpiar archivos generados"
    echo "  --install               Instalar dependencias"
    echo "  --setup-db              Configurar base de datos"
    echo "  --teardown-db           Limpiar base de datos"
    echo ""
    echo "Ejemplos:"
    echo "  $0                      # Ejecutar todas las pruebas (locales)"
    echo "  $0 -u                   # Solo pruebas unitarias"
    echo "  $0 -c -r                # Pruebas con cobertura y reportes"
    echo "  $0 -d -u                # Unitarias en Docker (recomendado)"
    echo "  $0 -d                   # En Docker: suite completa (perfil full + infra)"
    echo "  $0 --install            # Instalar dependencias"
    echo ""
}

# Variables por defecto
TEST_TYPE="all"
COVERAGE=false
REPORT=false
DOCKER=false
VERBOSE=false
FAILED_ONLY=false
SLOW_ONLY=false
FAST_ONLY=false
CLEAN=false
INSTALL=false
SETUP_DB=false
TEARDOWN_DB=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            TEST_TYPE="unit"
            shift
            ;;
        -i|--integration)
            TEST_TYPE="integration"
            shift
            ;;
        -p|--performance)
            TEST_TYPE="performance"
            shift
            ;;
        -s|--security)
            TEST_TYPE="security"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--failed)
            FAILED_ONLY=true
            shift
            ;;
        --slow)
            SLOW_ONLY=true
            shift
            ;;
        --fast)
            FAST_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --setup-db)
            SETUP_DB=true
            shift
            ;;
        --teardown-db)
            TEARDOWN_DB=true
            shift
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Función para limpiar archivos generados
clean_files() {
    print_status "Limpiando archivos generados..."
    rm -rf reports/
    rm -rf htmlcov/
    rm -rf .pytest_cache/
    rm -rf .coverage
    rm -rf coverage.xml
    rm -rf .benchmarks/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Archivos generados limpiados"
}

# Función para instalar dependencias
install_dependencies() {
    print_status "Instalando dependencias..."
    if [ -f "install_test_dependencies.sh" ]; then
        ./install_test_dependencies.sh
    else
        print_error "Script de instalación no encontrado"
        exit 1
    fi
    print_success "Dependencias instaladas"
}

# Función para configurar base de datos
setup_database() {
    print_status "Configurando base de datos de prueba..."
    if command -v psql >/dev/null 2>&1; then
        psql -c "CREATE DATABASE test_db;" 2>/dev/null || echo "Base de datos ya existe"
        psql -c "CREATE USER test_user WITH PASSWORD 'test_pass';" 2>/dev/null || echo "Usuario ya existe"
        psql -c "GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;" 2>/dev/null || echo "Permisos ya otorgados"
    else
        print_warning "PostgreSQL no encontrado, usando mocks"
    fi
    print_success "Base de datos configurada"
}

# Función para limpiar base de datos
teardown_database() {
    print_status "Limpiando base de datos de prueba..."
    if command -v psql >/dev/null 2>&1; then
        psql -c "DROP DATABASE IF EXISTS test_db;" 2>/dev/null || true
        psql -c "DROP USER IF EXISTS test_user;" 2>/dev/null || true
    fi
    print_success "Base de datos limpiada"
}

# Función para ejecutar pruebas en Docker
run_docker_tests() {
    print_status "Ejecutando pruebas en Docker..."
    
    if [ ! -f "docker-compose.test.yml" ]; then
        print_error "Archivo docker-compose.test.yml no encontrado"
        exit 1
    fi

    if docker compose version >/dev/null 2>&1; then
        COMPOSE=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE=(docker-compose)
    else
        print_error "No se encontró «docker compose» ni «docker-compose»"
        exit 1
    fi

    COMPOSE_FILE=( -f docker-compose.test.yml )

    "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" build

    case $TEST_TYPE in
        unit)
            print_status "Modo: unitarias (sin levantar Postgres/MQTT/Influx/Redis)"
            "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" run --rm tests
            ;;
        integration)
            print_status "Modo: integración (perfil integration)"
            "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" --profile integration run --rm integration-tests
            ;;
        performance)
            print_status "Modo: rendimiento (perfil performance)"
            "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" --profile performance run --rm performance-tests
            ;;
        security)
            print_status "Modo: seguridad (perfil security)"
            "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" --profile security run --rm security-tests
            ;;
        all)
            print_status "Modo: suite completa tests/ (perfil full + servicios de apoyo)"
            "${COMPOSE[@]}" "${COMPOSE_FILE[@]}" --profile full run --rm tests-full
            ;;
    esac
    
    print_success "Pruebas en Docker completadas"
}

# Función para ejecutar pruebas locales
run_local_tests() {
    print_status "Ejecutando pruebas locales..."
    
    # Activar entorno virtual si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Entorno virtual activado"
    fi
    
    # Construir comando pytest
    PYTEST_CMD="pytest"
    
    # Agregar directorio de pruebas
    case $TEST_TYPE in
        "unit")
            PYTEST_CMD="$PYTEST_CMD tests/unit/"
            ;;
        "integration")
            PYTEST_CMD="$PYTEST_CMD tests/integration/"
            ;;
        "performance")
            PYTEST_CMD="$PYTEST_CMD tests/performance/"
            ;;
        "security")
            PYTEST_CMD="$PYTEST_CMD tests/security/"
            ;;
        "all")
            PYTEST_CMD="$PYTEST_CMD tests/"
            ;;
    esac
    
    # Agregar opciones
    if [ "$VERBOSE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -v -s"
    else
        PYTEST_CMD="$PYTEST_CMD -v"
    fi
    
    if [ "$COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov=src/iot_middleware --cov-report=term-missing"
        if [ "$REPORT" = true ]; then
            PYTEST_CMD="$PYTEST_CMD --cov-report=html"
        fi
    fi
    
    if [ "$REPORT" = true ]; then
        mkdir -p reports
        PYTEST_CMD="$PYTEST_CMD --html=reports/report.html --self-contained-html"
    fi
    
    if [ "$FAILED_ONLY" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --lf"
    fi
    
    if [ "$SLOW_ONLY" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -m slow"
    fi
    
    if [ "$FAST_ONLY" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
    fi
    
    # Ejecutar pruebas
    print_status "Comando: $PYTEST_CMD"
    eval $PYTEST_CMD
    
    print_success "Pruebas locales completadas"
}

# Función principal
main() {
    echo "🧪 Script de Ejecución de Pruebas - IoT Middleware"
    echo "=================================================="
    echo ""
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "conftest.py" ]; then
        print_error "Este script debe ejecutarse desde el directorio tests/"
        print_error "Asegúrate de estar en el directorio tests/ del proyecto"
        exit 1
    fi
    
    # Ejecutar acciones según los argumentos
    if [ "$CLEAN" = true ]; then
        clean_files
    fi
    
    if [ "$INSTALL" = true ]; then
        install_dependencies
    fi
    
    if [ "$SETUP_DB" = true ]; then
        setup_database
    fi
    
    if [ "$TEARDOWN_DB" = true ]; then
        teardown_database
    fi
    
    # Ejecutar pruebas
    if [ "$DOCKER" = true ]; then
        run_docker_tests
    else
        run_local_tests
    fi
    
    # Mostrar información de reportes
    if [ "$REPORT" = true ]; then
        echo ""
        echo "📊 Reportes generados:"
        if [ -f "reports/report.html" ]; then
            echo "  • HTML: reports/report.html"
        fi
        if [ -d "htmlcov" ]; then
            echo "  • Cobertura: htmlcov/index.html"
        fi
    fi
    
    print_success "¡Ejecución de pruebas completada! 🎉"
}

# Ejecutar función principal
main "$@"



