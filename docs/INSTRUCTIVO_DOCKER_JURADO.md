# Instructivo: verificación del stack con Docker Desktop (IoT Middleware)

Documento orientado a la constatación académica del despliegue del middleware IoT: comprobar que los contenedores existen, están sanos, se pueden levantar, parar y recrear de forma reproducible usando Docker Desktop como runtime oficial local.

Evidencias visuales recomendadas: [ANEXO_CAPTURAS_DOCKER_JURADO.md](./ANEXO_CAPTURAS_DOCKER_JURADO.md).

## 1. Objetivo

Demostrar que el sistema PaaS IoT está contenerizado y puede gestionarse con un pipeline claro de:

1. Chequeo de estado
2. Arranque y parada
3. Recreación del stack cuando cambia su definición

## 2. Prerrequisitos

| Requisito | Comprobación |
|-----------|--------------|
| Docker Desktop instalado y en ejecución | `docker --version` |
| Docker Compose disponible | `docker compose version` |
| Código del proyecto clonado | Directorio raíz con `infra/containers/docker-compose.yaml` y `scripts/docker-stack.sh` |

Dar permisos de ejecución al script si hiciera falta:

```bash
chmod +x scripts/docker-stack.sh
```

Todos los comandos asumen la raíz del repositorio como directorio de trabajo:

```bash
cd /ruta/al/iot-middleware
```

## 3. Arquitectura de contenedores

| Contenedor | Rol | Puerto(s) típico(s) |
|------------|-----|---------------------|
| `mosquitto` | Broker MQTT | 1883 |
| `influxdb` | Series temporales | 8086 |
| `postgresql` | Metadatos y datos relacionales | 5432 |
| `rabbitmq` | Mensajería | 5672, 15672 |
| `iotmw-api` | API FastAPI | 8000 |
| `iotmw-ingestor` | Servicio de ingesta | sin puerto publicado |
| `iotmw-dashboard` | UI + WebSocket | 8080 |
| `iotmw-admin` | Panel de administración | 9000 |

Definición formal del stack: `infra/containers/docker-compose.yaml`.

## 4. Pipeline de constatación

La ruta recomendada es `scripts/docker-stack.sh`.

### 4.1 Estado

```bash
./scripts/docker-stack.sh status
```

### 4.2 Healthcheck

```bash
./scripts/docker-stack.sh healthcheck
```

### 4.3 Sondas HTTP

```bash
./scripts/docker-stack.sh probe
```

### 4.4 Pipeline completo

```bash
./scripts/docker-stack.sh check
```

## 5. Levantar y parar el sistema

### 5.1 Levantar

```bash
./scripts/docker-stack.sh up
```

Equivalente manual:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

### 5.2 Parar

```bash
./scripts/docker-stack.sh down
```

### 5.3 Parar y eliminar contenedores

```bash
./scripts/docker-stack.sh down-remove
```

### 5.4 Recrear

```bash
./scripts/docker-stack.sh recreate
```

### 5.5 Reiniciar

```bash
./scripts/docker-stack.sh restart
```

### 5.6 Arranque manual

```bash
./scripts/docker-stack.sh start-manual
```

## 6. Inspección de logs

```bash
./scripts/docker-stack.sh logs iotmw-api
./scripts/docker-stack.sh logs postgresql
```

## 7. Guion sugerido para jurado

1. Contexto: el middleware corre en contenedores definidos en `infra/containers/docker-compose.yaml`.
2. Estado inicial: `./scripts/docker-stack.sh status`.
3. Arranque: `./scripts/docker-stack.sh up`.
4. Evidencia funcional: `./scripts/docker-stack.sh probe`.
5. Parada controlada: `./scripts/docker-stack.sh down`.
6. Recuperación: `./scripts/docker-stack.sh up` o `./scripts/docker-stack.sh recreate`.

## 8. Criterios de éxito

- `docker ps` responde correctamente.
- `status` muestra los servicios esperados.
- `probe` devuelve respuestas 2xx en API, admin y dashboard.
- `down` + `up` es reproducible.

## 9. Referencias

| Recurso | Ubicación |
|---------|-----------|
| Definición del stack | `infra/containers/docker-compose.yaml` |
| Script oficial | `scripts/docker-stack.sh` |
| Anexo de capturas | `docs/ANEXO_CAPTURAS_DOCKER_JURADO.md` |

El archivo [INSTRUCTIVO_PODMAN_JURADO.md](./INSTRUCTIVO_PODMAN_JURADO.md) queda solo como referencia histórica/deprecated.
