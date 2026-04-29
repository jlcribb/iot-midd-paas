# Control Engine Executive Summary

## Qué se demuestra

Midd IOT ya cuenta con un MVP técnico end-to-end de control paramétrico que:

- consume eventos reales desde RabbitMQ;
- evalúa control mediante `parametric-control-engine`;
- selecciona policies desde PostgreSQL por proyecto y contexto;
- emite recommendations;
- persiste y publica auditoría;
- expone observabilidad read-only;
- muestra resultados en un dashboard mínimo;
- genera benchmark operativo reproducible.

## Estado del MVP

Capacidades demostrables hoy:

- integración runtime no invasiva;
- feature flag por proyecto;
- policies persistentes por proyecto;
- auditoría persistente;
- dashboard `/control`;
- benchmark operativo con artefactos exportables.

## Evidencia actual

Resultados del benchmark operativo vigente:

- `policy_driven` logró el menor error medio absoluto agregado: `5.469`
- `proportional` logró el menor esfuerzo total agregado: `80.31`
- modo `disabled`: `0` recommendations + `3` skipped audits

## Valor ejecutivo

Esto permite mostrar que el sistema no es solo un prototipo teórico:

- opera sobre runtime real;
- deja trazabilidad auditable;
- puede demostrarse desde interfaz operacional;
- produce evidencia cuantitativa reproducible.

## Recorrido corto de demostración

1. Levantar stack:

```bash
docker compose -f infra/containers/docker-compose.yaml up -d
```

2. Ejecutar smoke real:

```bash
./scripts/smoke_control_engine_rabbitmq.sh
```

3. Abrir dashboard:

- [http://localhost:3000/control](http://localhost:3000/control)

4. Exportar benchmark:

```bash
PYTHONPATH=src ./venv/bin/python scripts/export_operational_control_benchmark.py
```

## Documento principal de demo

- [control_engine_demo_guide.md](./control_engine_demo_guide.md)
