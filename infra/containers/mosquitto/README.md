# Mosquitto en Docker

## Error: `the container name "mosquitto" is already in use`

Ocurre al usar `--force-recreate` cuando ya existe un contenedor con ese nombre **gestionado fuera del último `compose up`** (estado desincronizado).

**Opción A — Solo recrear Mosquitto (tiene dependientes `api` e `ingestor`):**

```bash
cd /ruta/al/iot-middleware   # raíz del repo, no uses el ejemplo "/ruta/al/..."
docker stop iotmw-api iotmw-ingestor mosquitto
docker rm -f iotmw-api iotmw-ingestor mosquitto
docker compose -f infra/containers/docker-compose.yaml up -d mosquitto api ingestor
```

**Opción B — Stack limpio (recomendado si Compose sigue chocando con nombres):** parar y borrar **todos** los contenedores del proyecto y volver a subirlos (los **volúmenes** de datos suelen conservarse):

```bash
cd /ruta/al/iot-middleware
docker compose -f infra/containers/docker-compose.yaml down
# Si quedan nombres huérfanos:
docker rm -f mosquitto influxdb postgresql rabbitmq iotmw-api iotmw-ingestor iotmw-dashboard iotmw-admin
docker compose -f infra/containers/docker-compose.yaml up -d
```

Orden al borrar manualmente: primero **dashboard** (depende de rabbitmq), luego **api/ingestor** (dependen de mosquitto/influx/postgres), luego el resto.

## Mensaje `chown: /mosquitto/data: Permission denied`

Lo genera el script de arranque de la imagen **eclipse-mosquitto** al ajustar permisos del directorio de datos. Suele ser **inofensivo**: si en el log aparece luego `mosquitto version … running`, el broker está activo.

**No** se debe montar **`tmpfs` en `/mosquitto/data`** además del volumen de la imagen: la imagen ya declara `VOLUME /mosquitto/data` y puede producir conflictos de montaje.

Si necesitas evitar por completo el aviso de `chown`, revisa la documentación de Docker sobre volúmenes y permisos en tu sistema operativo.

## Si el contenedor no arranca

1. **Logs del broker** (motivo real del fallo):

   ```bash
   docker logs mosquitto
   ```

2. **Puerto 1883 ocupado en el host** — otro proceso (otro Mosquitto, Home Assistant, etc.):

   ```bash
   lsof -i :1883
   ```

   Cambia el mapeo en `infra/containers/docker-compose.yaml` (ej. `"18830:1883"`) o libera el puerto.

3. **Compose desde la raíz del repo** — la ruta `./mosquitto/mosquitto.conf` es relativa al directorio del compose. Ejecuta:

   ```bash
   docker compose -f infra/containers/docker-compose.yaml up -d mosquitto
   ```

   desde la **raíz** del proyecto, no desde `infra/containers/` (si no, el volumen puede montar un archivo vacío o fallar).

4. **Recrear el contenedor** tras cambiar `mosquitto.conf`:

   ```bash
   docker compose -f infra/containers/docker-compose.yaml up -d --force-recreate mosquitto
   ```

Las rutas legacy `infra/containers/podman-compose.yaml` y `containers/podman-compose.yaml` se conservan solo como alias deprecated de compatibilidad.

5. **Permisos (host / volumen)** — si sigue fallando, revisa que el directorio de datos del volumen sea escribible por el usuario del proceso dentro de la imagen.

## Comprobar que escucha

```bash
docker exec mosquitto mosquitto_sub -h localhost -t '$SYS/broker/uptime' -C 1
```

(o desde el host: `mosquitto_sub -h 127.0.0.1 -p 1883 -t test -C 1` si tienes cliente instalado).
