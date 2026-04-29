# Makefile para Pruebas - IoT Middleware
# =====================================

.PHONY: help install test test-unit test-integration test-performance test-security test-coverage test-html test-report clean lint format check-deps setup-db teardown-db

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
COVERAGE := coverage
VENV := venv
TEST_DIR := tests
SRC_DIR := src/iot_middleware
REPORTS_DIR := reports
COVERAGE_DIR := htmlcov

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Ayuda
help: ## Mostrar ayuda
	@echo "$(BLUE)🧪 Makefile para Pruebas - IoT Middleware$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "$(GREEN)Comandos disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Ejemplos de uso:$(NC)"
	@echo "  make install          # Instalar dependencias"
	@echo "  make test             # Ejecutar todas las pruebas"
	@echo "  make test-unit        # Solo pruebas unitarias"
	@echo "  make test-coverage    # Pruebas con cobertura"
	@echo "  make test-html        # Generar reporte HTML"
	@echo "  make clean            # Limpiar archivos generados"

# Instalación
install: ## Instalar dependencias de pruebas
	@echo "$(BLUE)[INFO]$(NC) Instalando dependencias de pruebas..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(BLUE)[INFO]$(NC) Creando entorno virtual..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "$(BLUE)[INFO]$(NC) Activando entorno virtual..."
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	@. $(VENV)/bin/activate && $(PIP) install -r requirements.txt
	@. $(VENV)/bin/activate && $(PIP) install -r $(TEST_DIR)/requirements-test.txt
	@echo "$(GREEN)[SUCCESS]$(NC) Dependencias instaladas correctamente"

# Verificar dependencias
check-deps: ## Verificar que las dependencias estén instaladas
	@echo "$(BLUE)[INFO]$(NC) Verificando dependencias..."
	@. $(VENV)/bin/activate && $(PYTHON) -c "import pytest; print('pytest version:', pytest.__version__)"
	@. $(VENV)/bin/activate && $(PYTHON) -c "import pytest_cov; print('pytest-cov instalado')"
	@. $(VENV)/bin/activate && $(PYTHON) -c "import pytest_mock; print('pytest-mock instalado')"
	@echo "$(GREEN)[SUCCESS]$(NC) Todas las dependencias están instaladas"

# Configurar base de datos de prueba
setup-db: ## Configurar base de datos de prueba
	@echo "$(BLUE)[INFO]$(NC) Configurando base de datos de prueba..."
	@if command -v psql >/dev/null 2>&1; then \
		echo "$(BLUE)[INFO]$(NC) PostgreSQL encontrado, configurando..."; \
		psql -c "CREATE DATABASE test_db;" 2>/dev/null || echo "Base de datos ya existe"; \
		psql -c "CREATE USER test_user WITH PASSWORD 'test_pass';" 2>/dev/null || echo "Usuario ya existe"; \
		psql -c "GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;" 2>/dev/null || echo "Permisos ya otorgados"; \
	else \
		echo "$(YELLOW)[WARNING]$(NC) PostgreSQL no encontrado, usando mocks"; \
	fi
	@echo "$(GREEN)[SUCCESS]$(NC) Base de datos configurada"

# Limpiar base de datos de prueba
teardown-db: ## Limpiar base de datos de prueba
	@echo "$(BLUE)[INFO]$(NC) Limpiando base de datos de prueba..."
	@if command -v psql >/dev/null 2>&1; then \
		psql -c "DROP DATABASE IF EXISTS test_db;" 2>/dev/null || true; \
		psql -c "DROP USER IF EXISTS test_user;" 2>/dev/null || true; \
	fi
	@echo "$(GREEN)[SUCCESS]$(NC) Base de datos limpiada"

# Pruebas
test: ## Ejecutar todas las pruebas
	@echo "$(BLUE)[INFO]$(NC) Ejecutando todas las pruebas..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Todas las pruebas completadas"

test-unit: ## Ejecutar solo pruebas unitarias
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas unitarias..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/ -v -m unit
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas unitarias completadas"

test-integration: ## Ejecutar solo pruebas de integración
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas de integración..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/integration/ -v -m integration
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas de integración completadas"

test-performance: ## Ejecutar solo pruebas de rendimiento
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas de rendimiento..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/performance/ -v -m performance
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas de rendimiento completadas"

test-security: ## Ejecutar solo pruebas de seguridad
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas de seguridad..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/security/ -v -m security
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas de seguridad completadas"

# Pruebas con cobertura
test-coverage: ## Ejecutar pruebas con cobertura de código
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas con cobertura..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=xml
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas con cobertura completadas"

test-coverage-html: ## Ejecutar pruebas con cobertura HTML
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas con cobertura HTML..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)[SUCCESS]$(NC) Reporte de cobertura HTML generado en $(COVERAGE_DIR)/"

# Reportes
test-html: ## Generar reporte HTML de pruebas
	@echo "$(BLUE)[INFO]$(NC) Generando reporte HTML de pruebas..."
	@mkdir -p $(REPORTS_DIR)
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ --html=$(REPORTS_DIR)/report.html --self-contained-html
	@echo "$(GREEN)[SUCCESS]$(NC) Reporte HTML generado en $(REPORTS_DIR)/report.html"

test-report: ## Generar reporte completo (HTML + XML + JSON)
	@echo "$(BLUE)[INFO]$(NC) Generando reporte completo..."
	@mkdir -p $(REPORTS_DIR)
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ \
		--html=$(REPORTS_DIR)/report.html \
		--self-contained-html \
		--junitxml=$(REPORTS_DIR)/junit.xml \
		--json-report \
		--json-report-file=$(REPORTS_DIR)/report.json \
		--cov=$(SRC_DIR) \
		--cov-report=html \
		--cov-report=xml
	@echo "$(GREEN)[SUCCESS]$(NC) Reporte completo generado en $(REPORTS_DIR)/"

# Linting y formato
lint: ## Ejecutar linting del código
	@echo "$(BLUE)[INFO]$(NC) Ejecutando linting..."
	@. $(VENV)/bin/activate && flake8 $(SRC_DIR) $(TEST_DIR) --count --select=E9,F63,F7,F82 --show-source --statistics
	@. $(VENV)/bin/activate && flake8 $(SRC_DIR) $(TEST_DIR) --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(GREEN)[SUCCESS]$(NC) Linting completado"

format: ## Formatear código con black e isort
	@echo "$(BLUE)[INFO]$(NC) Formateando código..."
	@. $(VENV)/bin/activate && black $(SRC_DIR) $(TEST_DIR)
	@. $(VENV)/bin/activate && isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)[SUCCESS]$(NC) Código formateado"

format-check: ## Verificar formato del código
	@echo "$(BLUE)[INFO]$(NC) Verificando formato del código..."
	@. $(VENV)/bin/activate && black --check $(SRC_DIR) $(TEST_DIR)
	@. $(VENV)/bin/activate && isort --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)[SUCCESS]$(NC) Formato del código verificado"

# Análisis de código
pylint: ## Ejecutar pylint
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pylint..."
	@. $(VENV)/bin/activate && pylint $(SRC_DIR) --output-format=json --output=$(REPORTS_DIR)/pylint-report.json || true
	@echo "$(GREEN)[SUCCESS]$(NC) Pylint completado"

mypy: ## Ejecutar mypy
	@echo "$(BLUE)[INFO]$(NC) Ejecutando mypy..."
	@. $(VENV)/bin/activate && mypy $(SRC_DIR) --junit-xml=$(REPORTS_DIR)/mypy-report.xml || true
	@echo "$(GREEN)[SUCCESS]$(NC) MyPy completado"

# Seguridad
security: ## Ejecutar análisis de seguridad
	@echo "$(BLUE)[INFO]$(NC) Ejecutando análisis de seguridad..."
	@. $(VENV)/bin/activate && bandit -r $(SRC_DIR) -f json -o $(REPORTS_DIR)/bandit-report.json || true
	@. $(VENV)/bin/activate && safety check --json --output $(REPORTS_DIR)/safety-report.json || true
	@echo "$(GREEN)[SUCCESS]$(NC) Análisis de seguridad completado"

# Pruebas específicas por módulo
test-config: ## Ejecutar pruebas del módulo config
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas del módulo config..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/test_config/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas del módulo config completadas"

test-mqtt: ## Ejecutar pruebas del módulo mqtt
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas del módulo mqtt..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/test_mqtt/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas del módulo mqtt completadas"

test-input: ## Ejecutar pruebas del módulo input
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas del módulo input..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/test_input/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas del módulo input completadas"

test-storage: ## Ejecutar pruebas del módulo storage
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas del módulo storage..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/test_storage/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas del módulo storage completadas"

test-services: ## Ejecutar pruebas del módulo services
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas del módulo services..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/unit/test_services/ -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas del módulo services completadas"

# Pruebas con opciones específicas
test-verbose: ## Ejecutar pruebas con output verbose
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas con output verbose..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ -v -s
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas verbose completadas"

test-failed: ## Ejecutar solo las pruebas que fallaron anteriormente
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas que fallaron anteriormente..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ --lf -v
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas fallidas completadas"

test-slow: ## Ejecutar solo las pruebas lentas
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas lentas..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ -v -m slow
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas lentas completadas"

test-fast: ## Ejecutar solo las pruebas rápidas (excluir lentas)
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas rápidas..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ -v -m "not slow"
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas rápidas completadas"

# Limpieza
clean: ## Limpiar archivos generados
	@echo "$(BLUE)[INFO]$(NC) Limpiando archivos generados..."
	@rm -rf $(REPORTS_DIR)/
	@rm -rf $(COVERAGE_DIR)/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf coverage.xml
	@rm -rf htmlcov/
	@rm -rf .benchmarks/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(NC) Archivos generados limpiados"

clean-all: clean ## Limpiar todo incluyendo entorno virtual
	@echo "$(BLUE)[INFO]$(NC) Limpiando todo incluyendo entorno virtual..."
	@rm -rf $(VENV)/
	@echo "$(GREEN)[SUCCESS]$(NC) Limpieza completa realizada"

# Desarrollo
dev-setup: install setup-db ## Configurar entorno de desarrollo completo
	@echo "$(GREEN)[SUCCESS]$(NC) Entorno de desarrollo configurado"

dev-test: test-coverage-html test-html ## Ejecutar pruebas de desarrollo con reportes
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas de desarrollo completadas con reportes"

# CI/CD
ci-test: ## Ejecutar pruebas para CI/CD
	@echo "$(BLUE)[INFO]$(NC) Ejecutando pruebas para CI/CD..."
	@. $(VENV)/bin/activate && $(PYTEST) $(TEST_DIR)/ \
		--cov=$(SRC_DIR) \
		--cov-report=xml \
		--cov-report=term-missing \
		--junitxml=$(REPORTS_DIR)/junit.xml \
		--html=$(REPORTS_DIR)/report.html \
		--self-contained-html
	@echo "$(GREEN)[SUCCESS]$(NC) Pruebas de CI/CD completadas"

# Información
info: ## Mostrar información del entorno
	@echo "$(BLUE)🧪 Información del Entorno de Pruebas$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(GREEN)Pip:$(NC) $$($(PIP) --version)"
	@echo "$(GREEN)Pytest:$(NC) $$(. $(VENV)/bin/activate && $(PYTEST) --version)"
	@echo "$(GREEN)Directorio de pruebas:$(NC) $(TEST_DIR)"
	@echo "$(GREEN)Directorio de código:$(NC) $(SRC_DIR)"
	@echo "$(GREEN)Entorno virtual:$(NC) $(VENV)"
	@echo ""
	@if [ -d "$(VENV)" ]; then \
		echo "$(GREEN)Entorno virtual:$(NC) ✅ Instalado"; \
	else \
		echo "$(GREEN)Entorno virtual:$(NC) ❌ No instalado"; \
	fi
	@if [ -f "$(TEST_DIR)/requirements-test.txt" ]; then \
		echo "$(GREEN)Requirements de pruebas:$(NC) ✅ Encontrado"; \
	else \
		echo "$(GREEN)Requirements de pruebas:$(NC) ❌ No encontrado"; \
	fi
	@if [ -f "$(TEST_DIR)/pytest.ini" ]; then \
		echo "$(GREEN)Configuración pytest:$(NC) ✅ Encontrado"; \
	else \
		echo "$(GREEN)Configuración pytest:$(NC) ❌ No encontrado"; \
	fi



