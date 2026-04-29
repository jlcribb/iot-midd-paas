# 🚀 Guía Rápida: Iniciar Panel de Administración

## Opción 1: Usar Podman Compose (Recomendado)

### Paso 1: Iniciar la máquina de Podman

```bash
# Verificar estado de la máquina
podman machine list

# Si no hay máquina, crear una
podman machine init

# Iniciar la máquina
podman machine start
```

### Paso 2: Iniciar el servicio admin

```bash
cd containers

# Usar 'podman compose' (sin guión) - versión integrada
podman compose up -d admin

# O si tienes podman-compose instalado por separado:
# podman-compose up -d admin
```

### Paso 3: Verificar que está corriendo

```bash
podman compose ps
# o
podman-compose ps
```

### Paso 4: Acceder a la interfaz

Abre tu navegador en: **http://localhost:9000**

## Opción 2: Desarrollo Local (sin contenedores)

Si prefieres ejecutar directamente sin contenedores:

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias del admin
pip install -r containers/admin/requirements.txt

# Configurar variables de entorno
export ADMIN_PORT=9000
export ADMIN_HOST=0.0.0.0
export CONFIG_PATH=config.yaml

# Asegurarse de que PostgreSQL esté corriendo
# (puedes usar podman compose solo para PostgreSQL)
cd containers
podman compose up -d postgresql

# Ejecutar el admin
cd ..
python -m containers.admin.main
```

## Opción 3: Instalar podman-compose (si prefieres el comando con guión)

```bash
# macOS con Homebrew
brew install podman-compose

# O con pip
pip install podman-compose

# Luego usar
podman-compose up -d admin
```

## Ver Logs

```bash
# Ver logs del servicio admin
podman compose logs -f admin

# O si usas podman-compose
podman-compose logs -f admin
```

## Detener el Servicio

```bash
podman compose down admin
# o
podman-compose down admin
```

## Troubleshooting

### Error: "Cannot connect to Podman"

```bash
# Iniciar la máquina de Podman
podman machine start

# Verificar conexión
podman ps
```

### Error: "command not found: podman-compose"

Usa `podman compose` (sin guión) en su lugar, o instala podman-compose:

```bash
# macOS
brew install podman-compose

# Linux
pip install podman-compose
```

### Error: Puerto 9000 en uso

```bash
# Ver qué está usando el puerto
lsof -i :9000

# Cambiar el puerto en podman-compose.yaml
# O usar otra variable de entorno
export ADMIN_PORT=9001
```
