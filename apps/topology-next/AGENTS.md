# AGENTS.md — Topology Next (Operational Domain)

## Objetivo del módulo

Exponer el dominio operacional del sistema.

Incluye:
- topología
- estado del sistema
- visualización de control

## Responsabilidades

- exponer APIs
- mostrar estado del sistema
- visualizar recomendaciones
- permitir configuración básica

## Reglas obligatorias

R1 No implementar lógica de control  
R2 No consumir directamente datos sin pasar por APIs  
R3 Mantener separación UI / lógica  
R4 No duplicar lógica backend  

## Control Integration

Debe:

- mostrar recomendaciones
- mostrar estado del control engine
- mostrar auditoría básica

## APIs

Ejemplo:

GET /api/control/recommendations  
GET /api/control/status  

## UI

Debe ser mínima:

- lista de recomendaciones
- estado del motor
- variables monitoreadas

## Prohibido

NO implementar lógica de control en frontend  
NO hacer UI compleja innecesaria  
NO consumir directamente bases de datos  

## Definition of Done

✔ endpoint funcional  
✔ datos visibles  
✔ integración con runtime  
✔ sin lógica duplicada  