# AGENTS.md — Infrastructure / Containers

## Objetivo del módulo

Definir entorno de ejecución del sistema.

Incluye:
- MQTT
- RabbitMQ
- PostgreSQL
- InfluxDB

## Responsabilidades

- levantar servicios
- garantizar conectividad
- mantener consistencia de entorno

## Reglas obligatorias

R1 No incluir lógica de negocio  
R2 No modificar configuraciones sin necesidad  
R3 Mantener compatibilidad con Docker Compose estándar  
R4 Toda configuración debe ser compatible con Docker Compose estándar  
R5 Evitar features exclusivas de Podman  

## Prohibido

NO cambiar tecnologías base  
NO introducir nuevas dependencias sin justificación  
NO modificar puertos sin coordinación  
NO introducir dependencias específicas de Podman  

## Definition of Done

✔ servicios levantan correctamente  
✔ comunicación funcional  
✔ entorno reproducible  

## Runtime oficial

Container runtime: Docker Desktop

Comando oficial:

```bash
docker compose
```
