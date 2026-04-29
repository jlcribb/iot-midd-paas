# infra/containers

Ubicacion canonica de la infraestructura local del proyecto.

Contenido actual:

- `infra/containers/docker-compose.yaml`
- `infra/containers/mosquitto/`
- `infra/containers/postgresql/`
- `infra/containers/influxdb/`

Compatibilidad temporal mantenida:

- `infra/containers/podman-compose.yaml`
- `containers/podman-compose.yaml`
- `containers/mosquitto -> ../infra/containers/mosquitto`
- `containers/postgresql -> ../infra/containers/postgresql`
- `containers/influxdb -> ../infra/containers/influxdb`

Comando canonico:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

Los archivos `*podman-compose.yaml` quedan solo como alias deprecated de compatibilidad. No usarlos como entrypoint operativo.
