> Architecture Package v0.2 — Estado: `APPROVED`.
> Clase estratégica: A1 — Digital Twin Foundation. R1 resolvió el baseline: `STEP_0_GATE = PASS`. Implementación completada con advertencias no bloqueantes; véase el [informe final](GDSS-001-FINAL-REPORT.md). Los requisitos originales se conservan; la matriz RBAC concretada está en la [guía de implementación](GDSS-001-IMPLEMENTATION.md).
> Este documento especifica requisitos arquitectónicos aprobados; no describe capacidades GDSS implementadas.

# 1. Modelo conceptual

```text
SystemModelIdentity
        │
        ├── SystemModelVersion 1
        ├── SystemModelVersion 2
        └── SystemModelVersion N
                    │
                    ├── Components
                    ├── Variables
                    ├── Parameters
                    ├── Formulas
                    ├── Constraints
                    └── Boundaries
```

Identidad y contenido versionado deberán permanecer separados.

R1/R2: `SystemModelVersion` es el aggregate root versionado. Cada `Component`, `Variable`, `Parameter`, `Formula`, `Constraint` y `Boundary` pertenece exactamente a una versión mediante `model_version_id` obligatorio. Su referencia histórica combina la versión exacta y su identificador local. No existe versionado independiente de fórmulas en GDSS-001.

Las referencias entre hijos deberán resolverse dentro de la misma versión. Crear un sucesor copia el contenido con pertenencia a la nueva versión; no comparte hijos mutables con su predecesor.

---

# 2. `SystemModelIdentity`

Representa la identidad lógica estable de un modelo.

Campos mínimos:

```text
id
canonical_name
description
created_at
created_by
```

No contiene el contenido mutable/versionable del modelo.

---

# 3. `SystemModelVersion`

Representa una versión concreta cuyo contenido es editable únicamente en `DRAFT` y se congela al alcanzar `VALIDATED` (R5).

Campos mínimos:

```text
id
system_model_identity_id
version
lifecycle_status
provenance
validity_domain
content_hash
created_at
created_by
```

Desde `VALIDATED`, una corrección de contenido crea una nueva versión `DRAFT`. Las transiciones posteriores cambian el lifecycle y agregan auditoría, sin modificar contenido ni su hash. El lifecycle gobernante pertenece exclusivamente a `SystemModelVersion` (NB-04).

---

# 4. `Component`

Representa una unidad composicional genérica.

```text
id
model_version_id
symbol
label
description
component_type
metadata
```

`component_type` no deberá depender de enumeraciones hidropónicas, térmicas o industriales en el core.

---

# 5. `Variable`

Representa una cantidad semánticamente identificable.

```text
id
model_version_id
symbol
label
description
computational_role
epistemic_kind
unit
dimension
provenance
```

R3: `computational_role` declara el rol estructural (`INPUT`, `OUTPUT`, `STATE`, `AUXILIARY`, `EXTERNAL`). `epistemic_kind` declara la categoría epistemológica (`OBSERVED`, `SIMULATED`, `PREDICTED`, `DERIVED`, `CALIBRATED`, `COUNTERFACTUAL`). No hay conversión automática ni inferencia entre ambos ejes. `OBSERVED` representa la categoría observada/medida frente a `PREDICTED`.

Por ejemplo, `INPUT` puede acompañar a `OBSERVED` y `OUTPUT` a `SIMULATED`; el rol no determina la categoría. En GDSS-001 todos estos valores son declaraciones; `STATE` no habilita integración temporal ni los demás roles habilitan ejecución o vinculación operacional.

---

# 6. `Parameter`

Representa una cantidad configurable del modelo.

```text
id
model_version_id
symbol
label
description
unit
dimension
default_value
valid_range
provenance
```

Un parámetro no debe confundirse con una observación.

---

# 7. `Formula`

Representa una relación declarativa.

GDSS-001 almacena su declaración, pero **no ejecuta ni interpreta expresiones arbitrarias**.

```text
id
model_version_id
symbol
description
expression_source
input_refs
output_ref
provenance
validity_domain
```

`expression_source` permanece declarativo hasta GDSS-002.

No se utilizará `eval`.

Su versión histórica y lifecycle son los del aggregate propietario. No tiene `lifecycle_status` independiente (NB-04).

---

# 8. `Constraint`

Representa una restricción declarada.

Campos mínimos de pertenencia: `id`, `model_version_id`. Toda referencia a otros hijos se limita a esa versión (R2).

Puede describir:

```text
range
compatibility
required relationship
boundary condition
domain validity
```

No ejecutará control.

---

# 9. `Boundary`

Declara qué pertenece al sistema y qué se considera externo.

```text
id
model_version_id
name
description
boundary_type
included_components
external_interfaces
```

Su función es semántica, no operacional.

---

# 10. `Provenance`

Toda entidad científicamente significativa deberá declarar origen.

Taxonomía inicial:

```text
LITERATURE
EMPIRICAL
DERIVED
CALIBRATED
HUMAN_PROPOSED
AI_PROPOSED
```

La procedencia original nunca deberá perderse mediante composición.

NB-03: la composición preserva y agrega las procedencias de los elementos sin promoción epistemológica. La procedencia propia del modelo no sustituye las de sus hijos ni las reduce a una categoría única.

---

# 11. `LifecycleStatus`

Lifecycle canónico inicial:

```text
DRAFT
  ↓
VALIDATED
  ↓
EXPERIMENTAL
  ↓
APPROVED
  ↓
PUBLISHED
  ↓
DEPRECATED
```

No se permiten saltos arbitrarios.

R4: `VALIDATED` significa que el artefacto superó las validaciones estructurales y de gobernanza exigibles a la fase actual. No implica validación científica, empírica, predictiva ni operacional:

```text
VALIDATED ≠ SCIENTIFICALLY_VALIDATED
VALIDATED ≠ EMPIRICALLY_CONFIRMED
VALIDATED ≠ OPERATIONALLY_SAFE
```

R5: sólo `DRAFT` admite edición autorizada. `VALIDATED`, `EXPERIMENTAL`, `APPROVED`, `PUBLISHED` y `DEPRECATED` conservan el contenido congelado. Crear un sucesor `DRAFT` no revierte el estado del original. Inmutabilidad del contenido y transición de lifecycle son operaciones diferentes.

NB-05: el Implementation Plan deberá definir permisos para crear, editar `DRAFT`, validar, promover a `EXPERIMENTAL`, aprobar, publicar y deprecar, con actor y auditoría. Deberá contrastarlos con el modelo de gobernanza de Midd-IoT y establecer la separación de autoridad aplicable. Ser creador no concede automáticamente permiso de publicación. La matriz RBAC concreta queda pendiente de planificación.

---

# 12. `UnitDefinition`

Campos:

```text
symbol
name
dimension
scale
offset
canonical_unit
```

Ejemplos futuros:

```text
m
s
kg
K
°C
Pa
L
mol
W
J
```

---

# 13. `Dimension`

La dimensionalidad se representa independientemente de la unidad concreta.

Ejemplo conceptual:

```text
LENGTH
TIME
MASS
TEMPERATURE
AMOUNT
CURRENT
LUMINOUS_INTENSITY
```

y dimensiones derivadas. NB-02: `DimensionSignature` representa exponentes de dimensiones base, no una enumeración cerrada de nombres derivados. Por ejemplo, velocidad = `L T^-1`, presión = `M L^-1 T^-2` y energía = `M L^2 T^-2`; una cantidad adimensional tiene todos los exponentes cero. El plan fijará representación numérica, normalización y serialización de la firma.

GDSS-001 valida declaraciones y compatibilidad explícita.

La validación algebraica completa corresponde a GDSS-002.

---

# 14. Objetos explícitamente inexistentes en GDSS-001

No deberán existir todavía contratos runtime para:

```text
SimulationRun
Solver
Actuator
ActuationCommand
Recommendation
ControlPolicy
TelemetryBinding
PhysicalBinding
DigitalTwinRuntime
CounterfactualRun
CalibrationRun
```

Algunos nombres podrán reservarse documentalmente, pero no implementarse prematuramente.
