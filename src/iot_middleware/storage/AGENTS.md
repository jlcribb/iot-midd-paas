# AGENTS.md — Storage Layer

## Objetivo del módulo

Gestionar persistencia de datos del sistema.

Incluye:
- PostgreSQL
- InfluxDB
- operaciones de escritura/lectura

## Responsabilidades

- persistir telemetría
- persistir auditoría
- exponer interfaces de acceso

## Reglas obligatorias

R1 No implementar lógica de negocio  
R2 No transformar datos semánticamente  
R3 Mantener consistencia entre DBs  
R4 Respetar contratos de escritura  

## Interfaces

- write_telemetry()
- write_audit()
- read_data()

## Prohibido

NO aplicar lógica de control  
NO modificar estructura de datos sin contrato  
NO acoplar a servicios  

## Definition of Done

✔ operación persistente correcta  
✔ datos consistentes  
✔ sin efectos secundarios  