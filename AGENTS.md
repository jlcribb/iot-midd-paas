# AGENTS.md — Midd IOT / Parametric Control Roadmap

## Objetivo no negociable

Evolucionar el PaaS IoT hacia una plataforma donde el `parametric-control-engine` sea una capacidad nativa, usable, auditable y habilitable por proyecto.

No realizar refactors grandes ni agregar features que no fortalezcan directamente:
- control paramétrico,
- políticas,
- auditoría,
- integración runtime,
- benchmark,
- dashboard operativo mínimo.

## Estado arquitectónico actual

- Python es el runtime oficial para ingesta, MQTT, storage y procesos IoT.
- Next.js en `apps/topology-next` es el backend oficial del dominio operacional.
- `apps/parametric-control-engine` es el frente principal del MVP.
- `core_backend` queda solo como transición bajo `/api/transition/core-backend/*`.
- `admin-fastapi` queda en mantenimiento mínimo.
- La API Python legacy para `/data`, `/topics`, `/stats`, `/dashboard` no debe expandirse.

## Regla principal

Toda nueva funcionalidad debe mapearse a una capacidad:

Core:
- C1 Ingesta IoT
- C2 Persistencia
- C3 Topología
- C4 Control Paramétrico
- C5 Políticas
- C6 Auditoría
- C7 Dashboard

Avanzadas:
- A1 Gemelo Digital
- A2 Benchmark
- A3 Cognitive Core
- A4 Agente IA

Si una tarea no fortalece una de estas capacidades, no implementarla.

## Flujo canónico de control

No crear flujos paralelos.

Telemetry Event
→ ControlEvaluationRequest
→ Policy Selection
→ Evaluation
→ Recommendation
→ Publishable Envelope
→ Audit Envelope

## Próxima implementación prioritaria

Implementar una integración no invasiva entre el runtime Python y `apps/parametric-control-engine`.

Crear o completar:

- `src/iot_middleware/services/control_engine_worker.py`
- adaptador de evento runtime → control request
- publicación de recomendaciones
- publicación/persistencia de auditoría
- feature flag por proyecto
- smoke test end-to-end

## Feature flag obligatorio

Agregar soporte para:

```sql
parametric_control_enabled BOOLEAN NOT NULL DEFAULT FALSE
```

## Runtime de contenedores local

Container runtime: Docker Desktop

CLI oficial:

```bash
docker
```

Compose oficial:

```bash
docker compose
```

No introducir dependencias específicas de Podman.
El stack debe ejecutarse mediante Docker Compose.
