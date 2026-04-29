# AGENTS.md — IoT Services

## Objetivo del módulo

Orquestar procesos runtime del sistema IoT.

Incluye:
- ingesta
- procesamiento
- integración con control engine

## Responsabilidades

- consumir eventos de telemetría
- enrutar eventos
- invocar control engine
- publicar resultados
- manejar errores

## Reglas obligatorias

R1 No implementar lógica de control aquí  
R2 Todo control debe delegarse a parametric-control-engine  
R3 No modificar estructura de eventos sin contrato  
R4 Todo flujo debe ser auditable  

## Control Engine Worker

Debe:

1. consumir eventos existentes
2. validar project_id
3. verificar feature flag
4. transformar evento → request
5. invocar control engine
6. publicar recommendation
7. publicar audit

## Feature Flags

Debe respetar:

- parametric_control_enabled
- ai_agent_enabled (futuro)

## Logging

Debe incluir:

- project_id
- variable
- valor
- resultado
- errores

## Prohibido

NO agregar lógica de negocio compleja  
NO duplicar evaluaciones  
NO acoplar a UI  
NO modificar contratos sin coordinación  

## Definition of Done

✔ flujo completo implementado  
✔ logs visibles  
✔ errores manejados  
✔ feature flag respetado  
✔ integración con engine funcionando  