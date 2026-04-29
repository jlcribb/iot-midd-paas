# Anexo: capturas de pantalla recomendadas (constatación con Docker)

Este anexo complementa [INSTRUCTIVO_DOCKER_JURADO.md](./INSTRUCTIVO_DOCKER_JURADO.md). Sirve para memoria del proyecto, informe escrito o anexo de evidencias.

## Lista de capturas

| # | Título sugerido | Momento / comando | Qué debe verse |
|---|-----------------|-------------------|----------------|
| 1 | Versión de Docker | `docker --version` | Versión instalada. |
| 2 | Compose disponible | `docker compose version` | Soporte Compose operativo. |
| 3 | Estado del stack | `./scripts/docker-stack.sh status` | Contenedores esperados y su estado. |
| 4 | Pipeline de chequeo | `./scripts/docker-stack.sh check` | Sondas HTTP correctas. |
| 5 | Lista Docker | `docker ps` | Contenedores del proyecto y puertos. |
| 6 | API OpenAPI | `http://127.0.0.1:8000/docs` | Swagger UI. |
| 7 | Panel admin | `http://127.0.0.1:9000/` | Pantalla principal del admin. |
| 8 | Dashboard health | `http://127.0.0.1:8080/health` | JSON de salud o vista principal. |
| 9 | RabbitMQ Management | `http://127.0.0.1:15672` | Login o panel. |
| 10 | Parada controlada | `./scripts/docker-stack.sh down` y luego `status` | Contenedores detenidos. |
| 11 | Recuperación | `./scripts/docker-stack.sh up` y luego `probe` | Sondas 2xx nuevamente. |
| 12 | Recreación | `./scripts/docker-stack.sh recreate` | Estado y sondas correctas. |
| 13 | Logs de un servicio | `./scripts/docker-stack.sh logs iotmw-api` o `docker logs --tail 30 iotmw-api` | Arranque sin errores fatales. |

## Orden sugerido

1. Herramienta y estado del stack.
2. Servicios expuestos.
3. Ciclo de vida del stack.
4. Logs técnicos.

## Nombres sugeridos

`01-docker-version.png`, `02-compose-version.png`, `03-stack-status-running.png` ... `13-api-logs.png`.

El archivo [ANEXO_CAPTURAS_JURADO.md](./ANEXO_CAPTURAS_JURADO.md) queda solo como referencia histórica/deprecated.
