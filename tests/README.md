# 🧪 Tests - IoT Middleware

## 📋 Descripción

Este directorio contiene todas las pruebas para el IoT Middleware, incluyendo pruebas unitarias, de integración, de rendimiento y de seguridad.

## 🏗️ Estructura

```
tests/
├── __init__.py                 # Paquete de pruebas
├── conftest.py                 # Configuración global de pytest
├── pytest.ini                 # Configuración de pytest
├── requirements-test.txt       # Dependencias para pruebas
├── README.md                   # Este archivo
├── fixtures/                   # Fixtures reutilizables
│   ├── __init__.py
│   ├── config_fixtures.py
│   ├── mqtt_fixtures.py
│   ├── database_fixtures.py
│   └── mock_fixtures.py
├── unit/                       # Pruebas unitarias
│   ├── __init__.py
│   ├── test_config/           # Pruebas del módulo config
│   ├── test_mqtt/             # Pruebas del módulo mqtt
│   ├── test_input/            # Pruebas del módulo input
│   ├── test_storage/          # Pruebas del módulo storage
│   ├── test_services/         # Pruebas del módulo services
│   ├── test_processing/       # Pruebas del módulo processing
│   ├── test_api/              # Pruebas del módulo api
│   ├── test_models/           # Pruebas del módulo models
│   └── test_utils/            # Pruebas del módulo utils
├── integration/                # Pruebas de integración
│   ├── __init__.py
│   ├── test_mqtt_integration.py
│   ├── test_input_integration.py
│   └── test_end_to_end.py
├── performance/                # Pruebas de rendimiento
│   ├── __init__.py
│   ├── test_load.py
│   └── test_stress.py
└── security/                   # Pruebas de seguridad
    ├── __init__.py
    ├── test_auth.py
    └── test_permissions.py
```

## 🚀 Instalación

### 1. Instalar Dependencias

```bash
# Instalar dependencias de pruebas
pip install -r tests/requirements-test.txt

# O instalar solo pytest
pip install pytest pytest-cov pytest-mock
```

### 2. Configurar Entorno

```bash
# Crear archivo de configuración de prueba
cp config.yaml tests/test_config.yaml

# Modificar configuración para pruebas
# (usar bases de datos de prueba, etc.)
```

## 🧪 Ejecución de Pruebas

### Ejecutar Todas las Pruebas

```bash
# Desde el directorio raíz del proyecto
pytest tests/

# Con cobertura de código
pytest tests/ --cov=src/iot_middleware --cov-report=html

# Con reporte detallado
pytest tests/ -v --tb=short
```

### Ejecutar Pruebas por Tipo

```bash
# Solo pruebas unitarias
pytest tests/unit/ -m unit

# Solo pruebas de integración
pytest tests/integration/ -m integration

# Solo pruebas de rendimiento
pytest tests/performance/ -m performance

# Solo pruebas de seguridad
pytest tests/security/ -m security
```

### Ejecutar Pruebas por Módulo

```bash
# Pruebas del módulo config
pytest tests/unit/test_config/

# Pruebas del módulo mqtt
pytest tests/unit/test_mqtt/

# Pruebas del módulo input
pytest tests/unit/test_input/

# Pruebas del módulo storage
pytest tests/unit/test_storage/

# Pruebas del módulo services
pytest tests/unit/test_services/
```

### Ejecutar Pruebas Específicas

```bash
# Prueba específica
pytest tests/unit/test_config/test_config_loader.py::TestConfigLoader::test_load_config_success

# Pruebas que contengan una palabra clave
pytest tests/ -k "config"

# Pruebas que fallen
pytest tests/ --lf

# Pruebas más lentas
pytest tests/ --durations=10
```

## 📊 Reportes

### Cobertura de Código

```bash
# Generar reporte de cobertura HTML
pytest tests/ --cov=src/iot_middleware --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html

# Generar reporte de cobertura en terminal
pytest tests/ --cov=src/iot_middleware --cov-report=term-missing
```

### Reportes HTML

```bash
# Generar reporte HTML de pruebas
pytest tests/ --html=reports/report.html --self-contained-html

# Ver reporte en navegador
open reports/report.html
```

### Reportes JSON

```bash
# Generar reporte JSON
pytest tests/ --json-report --json-report-file=reports/report.json
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Configurar entorno de pruebas
export TEST_ENV=true
export TEST_DB_URL=postgresql://test:test@localhost:5432/test_db
export TEST_MQTT_BROKER=localhost:1883
export TEST_INFLUXDB_URL=http://localhost:8086
```

### Archivo de Configuración

```yaml
# tests/test_config.yaml
mqtt:
  broker: localhost
  port: 1883
  topics: ['test/+/+']
influxdb:
  url: http://localhost:8086
  token: test_token
  org: test_org
  bucket: test_bucket
postgresql:
  host: localhost
  port: 5432
  database: test_db
  username: test_user
  password: test_pass
```

## 📋 Marcadores de Pruebas

### Marcadores Disponibles

- `@pytest.mark.unit` - Pruebas unitarias
- `@pytest.mark.integration` - Pruebas de integración
- `@pytest.mark.performance` - Pruebas de rendimiento
- `@pytest.mark.security` - Pruebas de seguridad
- `@pytest.mark.slow` - Pruebas lentas
- `@pytest.mark.mqtt` - Pruebas relacionadas con MQTT
- `@pytest.mark.database` - Pruebas relacionadas con base de datos
- `@pytest.mark.api` - Pruebas relacionadas con API
- `@pytest.mark.input` - Pruebas relacionadas con input
- `@pytest.mark.config` - Pruebas relacionadas con configuración

### Uso de Marcadores

```python
import pytest

@pytest.mark.unit
def test_unit_function():
    """Prueba unitaria"""
    pass

@pytest.mark.integration
def test_integration_flow():
    """Prueba de integración"""
    pass

@pytest.mark.performance
def test_performance_load():
    """Prueba de rendimiento"""
    pass

@pytest.mark.security
def test_security_auth():
    """Prueba de seguridad"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Prueba lenta"""
    pass
```

## 🎯 Criterios de Éxito

### Métricas de Calidad

- **Cobertura de código**: ≥ 80%
- **Pruebas unitarias**: ≥ 200 casos
- **Pruebas de integración**: ≥ 50 casos
- **Tiempo de ejecución**: ≤ 5 minutos
- **Tasa de éxito**: ≥ 95%

### Estándares de Código

- **Pylint**: ≥ 8.0
- **Black**: Formato consistente
- **isort**: Imports ordenados
- **flake8**: Sin errores

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    - name: Run tests
      run: pytest tests/ --cov=src/iot_middleware --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Ejecución Local

```bash
# Ejecutar pruebas como en CI
pytest tests/ --cov=src/iot_middleware --cov-report=xml --junitxml=reports/junit.xml
```

## 🐛 Debugging

### Ejecutar Pruebas en Modo Debug

```bash
# Con output detallado
pytest tests/ -v -s

# Con pdb en fallos
pytest tests/ --pdb

# Con pdb en todos los casos
pytest tests/ --pdbcls=IPython.terminal.debugger:Pdb
```

### Logging en Pruebas

```python
import logging

def test_with_logging():
    """Prueba con logging"""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Ejecutando prueba")
    # ... resto de la prueba
```

## 📚 Recursos

### Documentación

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)

### Mejores Prácticas

- **Nombres descriptivos**: `test_should_return_error_when_invalid_input`
- **Una aserción por prueba**: Cada prueba debe verificar una cosa
- **Fixtures reutilizables**: Usar fixtures para datos de prueba
- **Mocks apropiados**: Mockear dependencias externas
- **Cobertura completa**: Probar casos de éxito y error

## 🤝 Contribución

### Agregar Nuevas Pruebas

1. **Crear archivo de prueba** en el directorio apropiado
2. **Seguir convenciones** de nomenclatura
3. **Agregar fixtures** si es necesario
4. **Documentar** casos de prueba complejos
5. **Ejecutar pruebas** antes de commit

### Ejemplo de Prueba

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Pruebas para nueva funcionalidad"""
    
    def test_success_case(self, mock_config):
        """Prueba caso de éxito"""
        # Arrange
        expected_result = "success"
        
        # Act
        result = new_function(mock_config)
        
        # Assert
        assert result == expected_result
    
    def test_error_case(self):
        """Prueba caso de error"""
        # Arrange
        invalid_input = None
        
        # Act & Assert
        with pytest.raises(ValueError):
            new_function(invalid_input)
    
    @pytest.mark.integration
    def test_integration_flow(self, mock_database):
        """Prueba flujo de integración"""
        # Implementar prueba de integración
        pass
```

---

**¡Las pruebas son fundamentales para mantener la calidad del código!** 🧪✨
