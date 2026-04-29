# AGENTS.md — Parametric Control Engine

## Objetivo del módulo

Implementar la lógica de control paramétrico del sistema.

Este módulo es la única fuente válida de:
- evaluación de control;
- generación de recomendaciones;
- trazabilidad de decisiones.

## Responsabilidades

- Evaluar eventos de telemetría
- Aplicar políticas de control
- Generar recomendaciones
- Generar trazabilidad (trace)

## Reglas obligatorias

R1 Toda lógica de control debe implementarse como evaluator  
R2 No se permite lógica de control fuera de evaluators  
R3 Los adapters no pueden contener lógica de control  
R4 Toda evaluación debe generar trace completo  
R5 No modificar contratos sin actualizar tests  

## Estructura esperada

- contracts/
- evaluators/
- policies/
- adapters/
- sources/
- examples/
- tests/

## Evaluators

Cada evaluator debe:

- implementar evaluate()
- recibir ControlEvaluationRequest
- devolver ControlEvaluationResponse
- incluir:
  - error
  - raw_control
  - recommendation
  - trace

## Policies

- Las políticas deben ser desacopladas del evaluator
- No hardcodear parámetros en evaluators
- Toda selección de política debe ser trazable

## Adapters

- Transforman datos entre sistemas
- No contienen lógica de control
- No deben tomar decisiones

## Tests

- Cada evaluator debe tener test
- No se permite agregar evaluators sin test
- Mantener cobertura funcional

## Prohibido

NO crear nuevos motores de control  
NO duplicar lógica de evaluación  
NO acoplar a runtime IoT directamente  
NO introducir dependencias externas innecesarias  

## Definition of Done

✔ evaluator implementado  
✔ test asociado  
✔ trace generado  
✔ contrato respetado  
✔ integración con adapter verificada  