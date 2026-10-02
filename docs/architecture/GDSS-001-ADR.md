> Architecture Package v0.2 — Estado: `APPROVED`.
> Clase estratégica: A1 — Digital Twin Foundation. R1 resolvió el baseline: `STEP_0_GATE = PASS`. Implementación completada con advertencias no bloqueantes; véase el [informe final](GDSS-001-FINAL-REPORT.md). Este documento conserva las decisiones arquitectónicas originales.
> Este documento especifica requisitos arquitectónicos aprobados; no describe capacidades GDSS implementadas.

## ADR — Governed Declarative Systems Foundation

### 1. Contexto

Midd-IoT requiere una representación formal de sistemas que permita evolucionar posteriormente hacia:

- sistemas dinámicos;
- simulación;
- experimentación;
- digital shadows;
- digital twins;
- comparación observed/simulated;
- calibración;
- investigación reproducible.

Esta capacidad no deberá derivarse del motor de control existente ni del DTE experimental.

El repositorio ya dispone de una línea prioritaria de integración de control que incluye, entre otros elementos:

- feature flag introducido en migración `0007`;
- `control_engine_worker.py`;
- benchmark de primer orden;
- auditoría;
- mecanismos operacionales asociados.

GDSS deberá permanecer arquitectónicamente ortogonal a esa línea.

---

## 2. Decisión

Crear **GDSS — Governed Dynamic Systems & Simulation** como subsistema independiente.

Su primera fase:

> **GDSS-001 — Governed Declarative Systems Foundation**

implementará exclusivamente representación declarativa, identidad, versionado, procedencia, lifecycle, unidades, dimensiones, restricciones y auditoría.

GDSS-001 **no ejecutará modelos**.

---

## 3. Principio rector

> **The core knows systems; domain packages know domains.**

Por tanto, el core puede conocer:

```text
SystemModel
Component
Variable
Parameter
Formula
Constraint
Boundary
Unit
Dimension
Provenance
Lifecycle
Version
```

pero no:

```text
Plant
Nutrient
Greenhouse
Tank
Pump
Room
HVAC
Battery
Hydroponics
```

Estos últimos son conceptos de dominio.

---

## 4. Decisión sobre Stock y Flow

`Stock` y `Flow` no serán primitivas obligatorias de GDSS-001.

Razón:

Su incorporación temprana podría sesgar el núcleo hacia System Dynamics/Forrester.

GDSS-001 debe ser suficientemente general para soportar posteriormente múltiples formalismos.

Se reservan para una futura capa de semántica dinámica.

---

## 5. Separación respecto del Control Engine

El `parametric-control-engine` continúa siendo responsable de su función actual.

En particular:

```text
first_order.py
```

permanece como benchmark de control.

No deberá:

- trasladarse a GDSS;
- convertirse en solver GDSS;
- convertirse en modelo base GDSS;
- definir contratos GDSS.

Una futura integración deberá realizarse mediante interfaces explícitas.

---

## 6. Separación respecto del DTE

El DTE existente posee naturaleza experimental y expone modos/comandos operacionales.

Por ello no será reutilizado como infraestructura GDSS-001.

Queda prohibida una integración implícita basada únicamente en similitud funcional.

Una eventual relación requerirá un ADR específico.

---

## 7. Dependencias prohibidas

El core GDSS no deberá importar directamente:

```text
control engine
DTE
MQTT
deployment execution
runtime binding
physical actuation
device commands
```

Esta restricción deberá verificarse automáticamente.

---

## 8. Frontera epistemológica

GDSS deberá preservar desde su origen:

```text
OBSERVED
SIMULATED
PREDICTED
DERIVED
CALIBRATED
COUNTERFACTUAL
```

como conceptos semánticamente diferentes.

GDSS-001 no necesita producir todos estos estados.

Debe impedir que su futura incorporación obligue a colapsarlos.

---

## 9. Formula ≠ Rule ≠ Policy

GDSS-001 define `Formula`.

No reutilizará:

- reglas de control;
- políticas operacionales;
- recomendaciones;
- decisiones de actuación.

Se reserva explícitamente:

```text
Formula ≠ Rule ≠ Policy
```

Una fórmula expresa una relación computacional.

No posee autoridad decisional.

---

## 10. Consecuencias

### Positivas

- independencia del dominio;
- ausencia de autoridad física;
- reutilización futura;
- trazabilidad;
- versionado;
- composición;
- evolución hacia Digital Twin;
- menor acoplamiento.

### Costos

- mayor formalización inicial;
- necesidad de contratos rigurosos;
- versionado explícito;
- posterior construcción de parser y runtime propios.

Estos costos se consideran aceptables.

---

## 11. Decisión final

**ACCEPT IF:**

1. GDSS puede existir sin Control Engine.
2. GDSS puede existir sin DTE.
3. GDSS puede existir sin MQTT.
4. dos dominios heterogéneos pueden expresarse mediante los mismos contratos;
5. el core permanece libre de vocabulario específico de dominio.

## 12. Remediaciones de Architectural Review v0.1

La revisión de v0.1 emitió `APPROVED_WITH_REQUIRED_REMEDIATIONS`. Esta v0.2 aplica las remediaciones documentales. El Implementation Plan v0.1 aportado por el usuario establece explícitamente Architecture Package v0.2 como baseline `APPROVED`; se registra aquí esa aprobación. No constituye autorización de implementación ni evidencia de enforcement.

| Hallazgo | Decisión v0.2 | Especificación |
|---|---|---|
| R1 | `SystemModelVersion` es el aggregate root versionado. Los hijos se versionan por pertenencia a esa versión; no hay `FormulaIdentity/FormulaVersion`. | [CONTRACTS](GDSS-001-CONTRACTS.md), GDS-INV-06 |
| R2 | Todos los hijos tienen `model_version_id` obligatorio y referencias limitadas a su propia versión. | [CONTRACTS](GDSS-001-CONTRACTS.md), [PERSISTENCE](GDSS-001-PERSISTENCE.md) |
| R3 | `computational_role` y `epistemic_kind` son ejes independientes. | CONTRACTS, GDS-INV-22 |
| R4 | `VALIDATED` acredita validaciones estructurales y de gobernanza de la fase; no validación científica. | CONTRACTS, GDS-INV-21 |
| R5 | Sólo `DRAFT` admite edición autorizada. Desde `VALIDATED` el contenido queda congelado; modificarlo requiere sucesor `DRAFT`. | PERSISTENCE, [INVARIANTS](GDSS-001-INVARIANTS.md) |
| NB-01 | La canonicalización distingue colecciones sin orden y secuencias con orden semántico. | PERSISTENCE; detalle por campo pendiente del plan |
| NB-02 | Dimensiones base y derivadas se representan con firmas de exponentes. | CONTRACTS; precisión y serialización pendientes del plan |
| NB-03 | Preservación y agregación de procedencia sin promoción epistemológica. | CONTRACTS, PERSISTENCE, INVARIANTS |
| NB-04 | El único lifecycle gobernante es el de `SystemModelVersion`; `Formula` no tiene estado independiente. | CONTRACTS, PERSISTENCE |
| NB-05 | El plan deberá definir permisos por operación y separación de autoridad según la gobernanza existente. Crear no confiere permiso para publicar. | CONTRACTS; RBAC pendiente del plan |

GDS-INV-01..20 se conservan, con reformulación explícita de GDS-INV-06. Se incorporan GDS-INV-21 y GDS-INV-22 en respuesta a R4 y R3, respectivamente.

El [Implementation Plan v0.1](GDSS-001-IMPLEMENTATION-PLAN.md) fue declarado aprobado por el [mandato MIDD-GDSS-P001](GDSS-001-OPERATIONAL-PROMPT.md). El bloqueo inicial de STEP 0 se conserva en el [informe histórico](GDSS-001-STEP-0-REPORT.md). R1 resolvió el baseline y P1–P4 antes de implementar; véanse la [reconciliación](GDSS-001-RECONCILIATION.md) y el [informe final](GDSS-001-FINAL-REPORT.md) para las decisiones NB concretadas y su evidencia.
