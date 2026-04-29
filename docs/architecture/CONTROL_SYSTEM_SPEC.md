1. Objetivo (NO modificable)
El sistema debe evolucionar hacia un PaaS IoT donde el control paramétrico sea una capacidad nativa, usable, auditable y habilitable por proyecto.

Cualquier desarrollo que no contribuya directamente a este objetivo queda fuera de alcance.
2. Capacidades del sistema
Core (obligatorias)
C1 Ingesta IoT
C2 Persistencia
C3 Topología
C4 Control Paramétrico
C5 Políticas
C6 Auditoría
C7 Dashboard
Avanzadas (opcionales)
A1 Gemelo Digital
A2 Benchmark
A3 Cognitive Core
A4 Agente IA
3. Reglas de desarrollo (CRÍTICAS)
R1 Ningún feature nuevo puede existir fuera de una capacidad.
R2 Ningún feature puede introducir un nuevo flujo paralelo.
R3 Toda lógica de control debe pasar por el parametric-control-engine.
R4 Toda decisión debe ser auditable.
R5 Toda salida debe tener un contrato definido.
R6 Ningún componente legacy puede expandirse.
R7 El sistema debe funcionar completamente sin IA.
4. Flujo oficial de control (canónico)
Telemetry Event
    → ControlEvaluationRequest
    → Policy Selection
    → Evaluation
    → Recommendation
    → Publishable Envelope
    → Audit Envelope

No se permiten variantes fuera de este flujo.

5. Feature gate por proyecto
project.parametric_control_enabled
project.ai_agent_enabled

Regla:

Si parametric_control_enabled = false
→ el motor no se ejecuta

Si ai_agent_enabled = false
→ no se expone ninguna funcionalidad IA
6. Evaluación de nuevas funcionalidades
Impacto (0–3)
Valor demostrable (0–3)
Complejidad (0–3)
Riesgo (0–3)

Score = (Impacto + Valor) - (Complejidad + Riesgo)

Regla:

Score ≤ 0 → RECHAZADO
Score 1–2 → BACKLOG
Score ≥ 3 → APROBADO
7. Lista explícita de NO HACER
NO crear nuevos motores de control paralelos
NO agregar IA sin caso de uso claro
NO expandir core_backend
NO agregar dashboards sin métricas de control
NO introducir nuevas bases de datos
NO romper el flujo canónico
NO acoplar el sistema a un proveedor de IA
8. Roadmap vinculante
Fase 1 → motor usable
Fase 2 → políticas
Fase 3 → integración completa
Fase 4 → benchmark
Fase 5 → cognitive core
Fase 6 → agente IA
9. Definición de DONE (muy importante)

Un feature está completo solo si:

✔ tiene contrato definido
✔ está integrado al flujo oficial
✔ es auditable
✔ es visible en dashboard (si aplica)
✔ está testeado
✔ está documentado
✔ no rompe capacidades existentes