# 🚀 Comandos para Ejecutar en tu Terminal

## ⚠️ Importante

El sandbox de Cursor tiene restricciones de permisos. **Ejecuta estos comandos directamente en tu terminal** (fuera de Cursor).

## ✅ Opción 3: Entorno Virtual (Recomendado)

### Método 1: Script Automático

```bash
# Desde el directorio del proyecto
cd /Users/joseluis/dev/iot-middleware

# Ejecutar script de configuración
./setup_venv.sh
```

### Método 2: Manual (Paso a Paso)

```bash
# 1. Ir al directorio del proyecto
cd /Users/joseluis/dev/iot-middleware

# 2. Eliminar venv existente si hay problemas
rm -rf venv

# 3. Crear entorno virtual
python3 -m venv venv

# 4. Activar entorno virtual
source venv/bin/activate

# 5. Actualizar pip
pip install --upgrade pip

# 6. Instalar dependencias principales
pip install -r requirements.txt

# 7. Instalar dependencias de testing
pip install -r tests/requirements-test.txt

# 8. Verificar instalación
pytest --version
```

## 🧪 Ejecutar Tests

Una vez instalado, puedes ejecutar tests:

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate

# Ejecutar tests de RabbitMQ
pytest tests/unit/test_messaging/ -v

# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Ejecutar con cobertura
pytest tests/ --cov=src/iot_middleware --cov-report=html
```

## 🔧 Solución de Problemas

### Error: "Permission denied"

Si tienes problemas de permisos, intenta:

```bash
# Dar permisos al directorio venv
chmod -R u+w venv/

# O recrear el entorno virtual
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Error: "No module named 'venv'"

```bash
# macOS
brew install python3

# O usar virtualenv
pip3 install virtualenv
virtualenv venv
```

### Error: "pip: command not found"

```bash
# Usar python3 -m pip
python3 -m pip install -r requirements.txt
```

---

**¡Ejecuta estos comandos en tu terminal!** 🚀
