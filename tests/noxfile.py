"""
Configuración de Nox para Pruebas - IoT Middleware
=================================================

Nox es una herramienta para automatizar pruebas en múltiples entornos Python.
"""

import nox
import os
import sys

# Versiones de Python a probar
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11"]

# Configuración por defecto
nox.options.sessions = ["tests", "lint", "format", "security", "coverage"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Ejecutar todas las pruebas"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas
    session.run("pytest", "tests/", "-v", "--cov=src/iot_middleware", "--cov-report=term-missing")


@nox.session(python="3.9")
def lint(session):
    """Ejecutar linting del código"""
    session.install("flake8", "pylint", "mypy")
    
    # flake8
    session.run("flake8", "src/iot_middleware", "tests/", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics")
    session.run("flake8", "src/iot_middleware", "tests/", "--count", "--exit-zero", "--max-complexity=10", "--max-line-length=127", "--statistics")
    
    # pylint
    session.run("pylint", "src/iot_middleware/", "--output-format=json", "--output=pylint-report.json")
    
    # mypy
    session.run("mypy", "src/iot_middleware/", "--junit-xml=mypy-report.xml")


@nox.session(python="3.9")
def format(session):
    """Verificar formato del código"""
    session.install("black", "isort")
    
    # Verificar formato con black
    session.run("black", "--check", "src/iot_middleware", "tests/")
    
    # Verificar orden de imports con isort
    session.run("isort", "--check-only", "src/iot_middleware", "tests/")


@nox.session(python="3.9")
def security(session):
    """Ejecutar análisis de seguridad"""
    session.install("bandit", "safety")
    
    # bandit
    session.run("bandit", "-r", "src/iot_middleware/", "-f", "json", "-o", "bandit-report.json")
    
    # safety
    session.run("safety", "check", "--json", "--output", "safety-report.json")


@nox.session(python="3.9")
def coverage(session):
    """Ejecutar pruebas con cobertura completa"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    session.install("coverage")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas con cobertura
    session.run("coverage", "run", "-m", "pytest", "tests/")
    session.run("coverage", "report", "--fail-under=80")
    session.run("coverage", "html")
    session.run("coverage", "xml")


@nox.session(python="3.9")
def unit_tests(session):
    """Ejecutar solo pruebas unitarias"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas unitarias
    session.run("pytest", "tests/unit/", "-v", "--cov=src/iot_middleware", "--cov-report=term-missing")


@nox.session(python="3.9")
def integration_tests(session):
    """Ejecutar solo pruebas de integración"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas de integración
    session.run("pytest", "tests/integration/", "-v", "--cov=src/iot_middleware", "--cov-append", "--cov-report=term-missing")


@nox.session(python="3.9")
def performance_tests(session):
    """Ejecutar solo pruebas de rendimiento"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas de rendimiento
    session.run("pytest", "tests/performance/", "-v", "--benchmark-only", "--benchmark-save=performance_results")


@nox.session(python="3.9")
def security_tests(session):
    """Ejecutar solo pruebas de seguridad"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    # Ejecutar pruebas de seguridad
    session.run("pytest", "tests/security/", "-v")


@nox.session(python="3.9")
def docs(session):
    """Generar documentación"""
    session.install("sphinx", "sphinx-rtd-theme")
    
    # Generar documentación
    session.run("sphinx-build", "-b", "html", "docs/", "docs/_build/html")


@nox.session(python="3.9")
def clean(session):
    """Limpiar archivos generados"""
    # Limpiar archivos de Python
    session.run("find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+")
    session.run("find", ".", "-type", "f", "-name", "*.pyc", "-delete")
    
    # Limpiar archivos de pruebas
    session.run("rm", "-rf", "reports/")
    session.run("rm", "-rf", "htmlcov/")
    session.run("rm", "-rf", ".pytest_cache/")
    session.run("rm", "-rf", ".coverage")
    session.run("rm", "-rf", "coverage.xml")
    session.run("rm", "-rf", ".benchmarks/")


@nox.session(python="3.9")
def install(session):
    """Instalar dependencias del proyecto"""
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Instalar en modo desarrollo
    session.install("-e", ".")


@nox.session(python="3.9")
def setup(session):
    """Configurar entorno de desarrollo"""
    # Instalar dependencias
    session.install("-r", "requirements.txt")
    session.install("-r", "tests/requirements-test.txt")
    
    # Configurar pre-commit
    session.install("pre-commit")
    session.run("pre-commit", "install")
    
    # Configurar variables de entorno
    session.env["TEST_ENV"] = "true"
    session.env["PYTHONPATH"] = os.path.join(session.virtualenv.location, "src")
    
    print("✅ Entorno de desarrollo configurado correctamente")
    print("📋 Comandos disponibles:")
    print("  • nox -s tests          # Ejecutar todas las pruebas")
    print("  • nox -s lint           # Ejecutar linting")
    print("  • nox -s format         # Verificar formato")
    print("  • nox -s security       # Análisis de seguridad")
    print("  • nox -s coverage       # Pruebas con cobertura")
    print("  • nox -s clean          # Limpiar archivos generados")






