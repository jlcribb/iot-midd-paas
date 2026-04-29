# 🧪 Instalación de Dependencias de Testing

## ⚠️ Problema Detectado

Si obtienes errores como:
- `zsh: command not found: pip`
- `SSLError: Operation not permitted`

Sigue estos pasos:

## ✅ Solución

### 1. Verificar Python y pip

```bash
# Verificar Python
python3 --version

# Verificar pip
python3 -m pip --version
```

### 2. Instalar Dependencias de Testing

**Opción A: Instalación Global (Recomendado para desarrollo)**

```bash
# Instalar dependencias de testing
python3 -m pip install -r tests/requirements-test.txt

# O si prefieres usar pip directamente (si está en PATH)
pip3 install -r tests/requirements-test.txt
```

**Opción B: Usar Entorno Virtual (Recomendado para producción)**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r tests/requirements-test.txt
```

### 3. Verificar Instalación

```bash
# Verificar que pytest esté instalado
python3 -m pytest --version

# O si usas entorno virtual
pytest --version
```

## 🔧 Solución de Problemas

### Error: "command not found: pip"

**Solución**: Usa `python3 -m pip` en lugar de `pip`:

```bash
# ❌ Incorrecto
pip install -r tests/requirements-test.txt

# ✅ Correcto
python3 -m pip install -r tests/requirements-test.txt
```

### Error: "Operation not permitted" (SSL)

**Solución**: Esto puede ser un problema de permisos o proxy. Intenta:

```bash
# Instalar sin verificar SSL (solo para desarrollo)
python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r tests/requirements-test.txt

# O actualizar pip primero
python3 -m pip install --upgrade pip
python3 -m pip install -r tests/requirements-test.txt
```

### Error: "Permission denied"

**Solución**: Usa `--user` para instalar en el directorio del usuario:

```bash
python3 -m pip install --user -r tests/requirements-test.txt
```

### Error: "No module named 'venv'"

**Solución**: Instala python3-venv:

```bash
# macOS
brew install python3

# Linux (Ubuntu/Debian)
sudo apt-get install python3-venv
```

## 📋 Comandos Rápidos

```bash
# 1. Verificar Python
python3 --version

# 2. Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
python3 -m pip install -r tests/requirements-test.txt

# 4. Verificar instalación
python3 -m pytest --version

# 5. Ejecutar tests
python3 -m pytest tests/unit/test_messaging/ -v
```

## 🎯 Próximos Pasos

Una vez instaladas las dependencias:

1. **Ejecutar tests de RabbitMQ**:
   ```bash
   python3 -m pytest tests/unit/test_messaging/ -v
   ```

2. **Ejecutar todos los tests unitarios**:
   ```bash
   python3 -m pytest tests/unit/ -v
   ```

3. **Ejecutar con cobertura**:
   ```bash
   python3 -m pytest tests/ --cov=src/iot_middleware --cov-report=html
   ```

## 💡 Recomendación

Para evitar problemas de permisos, **usa un entorno virtual**:

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar (macOS/Linux)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r tests/requirements-test.txt

# Ahora puedes usar pytest directamente
pytest tests/unit/test_messaging/ -v
```

---

**¡Ejecuta estos comandos directamente en tu terminal!** 🚀
