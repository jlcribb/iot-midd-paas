# MIDD-IOT — GDSS-001
## Governed Declarative Systems Foundation
### Implementation Plan v0.1

**Estado:** `APPROVED`
**Clase estratégica:** A1 — Digital Twin Foundation
**Baseline arquitectónico:** Architecture Package v0.2 — `APPROVED`
**Implementación:** `STEP_0_GATE = PASS`; `COMPLETED_GOVERNED_DECLARATIVE_SYSTEMS_FOUNDATION_WITH_WARNINGS`.

> Actualización de cierre 2026-10-02: MIDD-GDSS-P001-R1 resolvió la divergencia inicial de baseline y permitió completar la ejecución. Véanse la [reconciliación](GDSS-001-RECONCILIATION.md) y el [informe final con evidencia](GDSS-001-FINAL-REPORT.md). El [STEP 0](GDSS-001-STEP-0-REPORT.md), las secciones 42 y 44 y los requisitos en futuro se conservan como registro histórico del plan aprobado, no como estado operativo actual.

---

# 1. Propósito

GDSS-001 implementará la primera fundación declarativa y gobernada para representar sistemas en Midd-IoT.

La fase deberá proporcionar:

```text
SystemModelIdentity
SystemModelVersion
Component
Variable
Parameter
Formula
Constraint
Boundary
Provenance
UnitDefinition
DimensionDefinition
LifecycleEvent
```

sin introducir todavía ejecución dinámica.

GDSS-001 deberá permitir expresar modelos de dominios heterogéneos utilizando exactamente el mismo núcleo.

La fase no implementará simulación, control ni Digital Twin runtime.

---

# 2. Principio de implementación

La implementación deberá preservar:

```text
DECLARATION
    ≠
EXECUTION
    ≠
OBSERVATION
    ≠
PREDICTION
    ≠
RECOMMENDATION
    ≠
AUTHORIZATION
    ≠
ACTUATION
```

La existencia de un modelo declarativo no confiere ninguna capacidad operacional.

---

# 3. Aggregate Root

El aggregate root será:

```text
SystemModelVersion
```

La identidad lógica permanecerá separada:

```text
SystemModelIdentity
        │
        ├── Version 1
        ├── Version 2
        └── Version N
```

Cada versión contendrá exclusivamente sus propios:

```text
Components
Variables
Parameters
Formulas
Constraints
Boundaries
```

Los hijos no serán compartidos de manera mutable entre versiones.

---

# 4. Estrategia de versionado

## 4.1 Identity

`SystemModelIdentity` representa la continuidad conceptual del modelo.

Restricción propuesta:

```text
canonical_name UNIQUE
```

La identidad no contiene contenido científico versionable.

---

## 4.2 Version

Restricción:

```text
UNIQUE(system_model_identity_id, version_number)
```

Cada versión deberá identificar opcionalmente:

```text
predecessor_version_id
```

para reconstruir:

```text
v1 → v2 → v3
```

sin convertir esta relación en mutabilidad.

---

## 4.3 Child ownership

Todos los hijos deberán incluir:

```text
model_version_id NOT NULL
```

y no podrán existir fuera de un `SystemModelVersion`.

Se propondrá unicidad:

```text
UNIQUE(model_version_id, symbol)
```

para entidades con `symbol`.

---

# 5. Estrategia de persistencia

Se propone incorporar tablas equivalentes a:

```text
gdss_system_model_identity
gdss_system_model_version

gdss_component
gdss_variable
gdss_parameter
gdss_formula
gdss_constraint
gdss_boundary

gdss_provenance
gdss_lifecycle_event

gdss_unit_definition
gdss_dimension_definition
```

Los nombres finales deberán adaptarse a las convenciones existentes del repositorio.

---

# 6. Provenance

No se implementará provenance como un simple enum embebido cuando ello impida conservar múltiples fuentes.

Se propone:

```text
ProvenanceRecord
 ├── id
 ├── kind
 ├── source_reference
 ├── description
 ├── asserted_by
 ├── created_at
 └── metadata
```

con tipos iniciales:

```text
LITERATURE
EMPIRICAL
DERIVED
CALIBRATED
HUMAN_PROPOSED
AI_PROPOSED
```

Las entidades gobernadas podrán relacionarse con uno o más registros de provenance.

La implementación deberá garantizar:

```text
composition
    →
provenance union
    →
NO epistemic promotion
```

Ejemplo:

```text
LITERATURE
EMPIRICAL
AI_PROPOSED
```

no puede reducirse automáticamente a:

```text
LITERATURE
```

---

# 7. Referencias científicas

Cuando:

```text
kind = LITERATURE
```

deberá existir información suficiente para identificar la fuente.

El contrato deberá admitir al menos:

```text
source_reference
```

sin imponer todavía un único estándar bibliográfico.

Podrá representar posteriormente:

```text
DOI
PMID
URL
ISBN
repository identifier
document identifier
```

GDSS-001 no implementará resolución externa automática de estas referencias.

---

# 8. Units & Dimensions

## 8.1 DimensionSignature

Se implementará una representación canónica basada en exponentes de las siete dimensiones SI:

```text
MASS
LENGTH
TIME
CURRENT
TEMPERATURE
AMOUNT
LUMINOUS_INTENSITY
```

Ejemplo:

```text
pressure

MASS                +1
LENGTH              -1
TIME                -2
CURRENT              0
TEMPERATURE          0
AMOUNT               0
LUMINOUS_INTENSITY   0
```

Adimensional:

```text
0,0,0,0,0,0,0
```

---

# 9. Catálogo histórico de unidades

Para evitar que una modificación del catálogo cambie retrospectivamente un modelo congelado, GDSS-001 utilizará:

> **immutable unit/dimension definitions**

Una definición utilizada por una versión congelada no podrá modificarse semánticamente.

Una corrección deberá crear una nueva definición.

Por tanto:

```text
UnitDefinition v1
    ≠
UnitDefinition corrected v2
```

aunque ambas representen conceptualmente la misma unidad.

Las versiones de modelos conservarán referencia a la definición exacta utilizada.

---

# 10. Compatibilidad dimensional

GDSS-001 deberá resolver:

```text
same dimension signature
        →
DIMENSIONALLY_COMPATIBLE
```

Ejemplos:

```text
m ↔ m
PASS

°C ↔ K
DIMENSIONALLY_COMPATIBLE

m ↔ s
REJECT

Pa ↔ kg
REJECT
```

No se implementará todavía:

```text
formula dimensional inference
symbolic algebra
expression evaluation
automatic unit conversion in formulas
```

Eso pertenece a GDSS-002.

---

# 11. Formula storage

`Formula` almacenará:

```text
symbol
description
expression_source
input_refs
output_ref
provenance
validity_domain
```

pero:

```text
expression_source
```

será **opaque declarative content** para GDSS-001.

Está expresamente prohibido:

```text
eval
exec
dynamic import
arbitrary expression execution
```

No habrá parser matemático en GDSS-001.

---

# 12. Referencias internas

Las referencias entre:

```text
Formula
Variable
Parameter
Constraint
Boundary
Component
```

deberán pertenecer a la misma:

```text
SystemModelVersion
```

La implementación deberá impedir:

```text
Formula@v2 → Variable@v1
```

como referencia interna normal.

Esto deberá estar protegido donde sea razonable por:

```text
database constraints
+
service validation
+
tests
```

y no exclusivamente por validación de UI.

---

# 13. Computational Role

Taxonomía inicial:

```text
INPUT
OUTPUT
STATE
AUXILIARY
EXTERNAL
```

Su función será exclusivamente declarativa.

En particular:

```text
STATE
```

no implica que exista:

```text
integrator
solver
state transition runtime
simulation
```

---

# 14. Epistemic Kind

Taxonomía inicial:

```text
OBSERVED
SIMULATED
PREDICTED
DERIVED
CALIBRATED
COUNTERFACTUAL
```

No deberá existir inferencia automática entre:

```text
computational_role
        ↕
epistemic_kind
```

---

# 15. OBSERVED y MEASURED

Para evitar introducir dos taxonomías paralelas:

```text
OBSERVED
```

será el concepto epistemológico general.

`MEASURED` no se introducirá como `epistemic_kind` independiente en GDSS-001.

Conceptualmente:

```text
MEASURED
    ⊂
OBSERVED
```

podrá modelarse posteriormente mediante:

```text
observation acquisition method
```

cuando exista integración real de observaciones.

Por tanto GDS-INV-02 se interpretará durante GDSS-001 como:

> una predicción nunca puede representarse como una observación/medición.

---

# 16. Lifecycle

Máquina de estados:

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

Sólo estas transiciones estarán permitidas inicialmente.

---

# 17. Semántica de VALIDATED

`VALIDATED` significará exclusivamente:

```text
STRUCTURALLY_VALIDATED
+
GOVERNANCE_VALIDATED
```

No significa:

```text
SCIENTIFICALLY_VALIDATED
EMPIRICALLY_CONFIRMED
PREDICTIVELY_VALIDATED
OPERATIONALLY_SAFE
```

La transición no podrá alterar provenance.

---

# 18. Freeze boundary

`DRAFT` será el único estado editable.

La transición:

```text
DRAFT → VALIDATED
```

deberá realizar atómicamente:

```text
1. validate structure
2. validate required provenance
3. validate references
4. validate unit/dimension declarations
5. construct canonical representation
6. calculate content_hash
7. freeze governed content
8. transition lifecycle
9. append LifecycleEvent
```

Si falla cualquier operación:

```text
ROLLBACK
```

No podrá existir:

```text
VALIDATED + partially mutable content
```

---

# 19. Successor creation

Modificar contenido congelado requerirá:

```text
CREATE SUCCESSOR VERSION
```

La operación:

```text
create_successor(version_id)
```

deberá:

```text
create new SystemModelVersion
copy governed children
rebind child references to new children
preserve provenance
record predecessor
set lifecycle = DRAFT
```

El sucesor podrá editarse.

El original permanecerá intacto.

---

# 20. Content Hash

El hash deberá representar exclusivamente contenido gobernado semánticamente relevante.

Excluirá:

```text
technical UUID
created_at
updated_at
lifecycle_status
LifecycleEvent
incidental serialization ordering
```

Incluirá el contenido declarativo gobernado.

---

# 21. Canonicalization Registry

Se deberá definir explícitamente, antes de implementar hashing, una clasificación por campo:

```text
ORDERED
UNORDERED
SCALAR
REFERENCE
```

Ejemplo conceptual:

```text
formula.input_refs
    classification to be explicitly decided

component collection
    UNORDERED

provenance collection
    UNORDERED unless contract states otherwise
```

No se utilizará una función genérica que ordene recursivamente todas las listas.

---

# 22. Stable local references

El hash no deberá depender de UUID generados.

Las referencias internas utilizadas en canonicalización deberán resolverse mediante identificadores semánticos estables dentro de la versión.

Preferentemente:

```text
symbol
```

o un canonical local key.

Esto deberá permitir que dos modelos semánticamente idénticos creados independientemente produzcan el mismo hash.

---

# 23. Lifecycle Events

Cada transición generará exactamente un evento append-only con:

```text
model_version_id
from_status
to_status
actor
timestamp
reason
metadata
```

La transición y el evento se persistirán en la misma transacción.

No habrá:

```text
transition without event
event without successful transition
```

---

# 24. RBAC

La implementación deberá reutilizar, donde corresponda, el mecanismo de autorización existente en Midd-IoT y no crear una segunda identidad/autorización paralela.

El plan deberá mapear permisos equivalentes a:

```text
CREATE_GDSS_MODEL
EDIT_GDSS_DRAFT
VALIDATE_GDSS_MODEL
PROMOTE_GDSS_EXPERIMENTAL
APPROVE_GDSS_MODEL
PUBLISH_GDSS_MODEL
DEPRECATE_GDSS_MODEL
```

Regla mínima:

```text
CREATE permission
    ≠
PUBLISH permission
```

La separación de autoridad concreta deberá comprobarse contra la gobernanza existente antes de codificar.

---

# 25. API / Service Surface

GDSS-001 podrá exponer exclusivamente operaciones declarativas y de gobernanza.

Ejemplos:

```text
create_model_identity
create_draft_version
update_draft
validate_version
promote_experimental
approve_version
publish_version
deprecate_version
create_successor
get_model
list_versions
```

No deberá exponer:

```text
run_model
simulate
predict
recommend
bind_telemetry
bind_device
publish_mqtt
execute_command
authorize_actuation
```

---

# 26. Domain-neutral fixtures

Se implementarán al menos dos fixtures.

## A. Hydroponic

Ejemplos de vocabulario permitido exclusivamente en el fixture:

```text
nutrient_solution
water_temperature
electrical_conductivity
```

## B. Thermal

```text
room
internal_temperature
external_temperature
thermal_resistance
```

Ambos deberán utilizar:

```text
same contracts
same persistence
same lifecycle
same hashing
same validation
```

No se admitirá lógica:

```text
if domain == hydroponic
```

en el core.

---

# 27. Vocabulary independence test

Se deberá inspeccionar el código productivo del core GDSS para detectar vocabulario específico de fixtures.

La prueba deberá restringirse a las áreas donde ese vocabulario sería arquitectónicamente significativo y excluir:

```text
tests
fixtures
documentation
comments where appropriate
```

para evitar falsos positivos.

---

# 28. Dependency boundary test

CI deberá fallar si GDSS core importa directamente infraestructura perteneciente a:

```text
parametric-control-engine
DTE
MQTT publishing
deployment execution
runtime physical binding
physical actuation
device command infrastructure
```

---

# 29. Negative capability tests

Además de inspeccionar dependencias, los tests deberán comprobar que la superficie pública GDSS-001 no puede representar operaciones como:

```text
open valve
start pump
publish MQTT
execute command
deploy policy
authorize actuation
```

Esto deberá verificarse como **ausencia de capacidad**, no simplemente como ausencia de uso.

---

# 30. Invariant Test Plan

La implementación deberá proporcionar evidencia automatizada para los invariantes clasificados `ENFORCED` y `ENFORCED_PARTIAL`.

Cobertura mínima:

```text
GDS-INV-01
GDS-INV-02
GDS-INV-03
GDS-INV-04
GDS-INV-05
GDS-INV-06
GDS-INV-09
GDS-INV-10
GDS-INV-11
GDS-INV-12
GDS-INV-14
GDS-INV-16
GDS-INV-18
GDS-INV-19
GDS-INV-21
GDS-INV-22
```

Los `STRUCTURALLY_RESERVED` deberán verificarse documentalmente y mediante ausencia de implementaciones prematuras donde corresponda.

---

# 31. Tests de versionado

Casos obligatorios:

```text
create identity
create v1 DRAFT
edit v1 DRAFT              PASS
validate v1                PASS
edit v1 VALIDATED          REJECT

create successor v2
edit v2 DRAFT              PASS

v1 content unchanged       PASS
v1 hash unchanged          PASS

cross-version reference    REJECT
same-version reference     PASS
```

---

# 32. Tests de lifecycle

```text
DRAFT → VALIDATED          PASS
VALIDATED → EXPERIMENTAL   PASS
EXPERIMENTAL → APPROVED    PASS
APPROVED → PUBLISHED       PASS
PUBLISHED → DEPRECATED     PASS
```

y:

```text
DRAFT → APPROVED           REJECT
DRAFT → PUBLISHED          REJECT
PUBLISHED → DRAFT          REJECT
DEPRECATED → PUBLISHED     REJECT
```

---

# 33. Tests de atomicidad

Deberán introducirse fallos controlados para demostrar que:

```text
hash failure
event persistence failure
validation failure
database failure
```

no dejan estados intermedios.

En particular:

```text
VALIDATED without LifecycleEvent
```

deberá ser imposible.

---

# 34. Tests de hash

Deberán probarse:

```text
same semantic content
different UUIDs
    →
same hash
```

```text
unordered collection reordered
    →
same hash
```

```text
ordered semantic sequence reordered
    →
different hash
```

```text
semantic value changed
    →
different hash
```

```text
lifecycle changed
    →
same content hash
```

---

# 35. Tests de provenance

Obligatorios:

```text
AI_PROPOSED → VALIDATED
provenance remains AI_PROPOSED
```

```text
AI_PROPOSED → PUBLISHED
provenance remains AI_PROPOSED
```

y composición:

```text
LITERATURE
+
EMPIRICAL
+
AI_PROPOSED

→ all remain identifiable
```

---

# 36. Tests dimensionales

Como mínimo:

```text
m / m
compatible

°C / K
dimensionally compatible

m / s
incompatible

Pa / kg
incompatible

dimensionless / dimensionless
compatible
```

No se probará todavía inferencia algebraica de fórmulas.

---

# 37. Baseline regression

Antes y después de GDSS-001 deberán ejecutarse:

```text
existing build
existing type checks
existing unit tests
existing integration tests
existing governance tests
```

según las capacidades reales del repositorio.

GDSS-001 no podrá considerarse cerrado si rompe el baseline existente.

---

# 38. Orden propuesto de implementación

```text
STEP 0
Repository reconnaissance
        ↓
STEP 1
Contracts / enums / types
        ↓
STEP 2
Unit + Dimension catalogs
        ↓
STEP 3
Persistence migration
        ↓
STEP 4
Canonicalization + hashing
        ↓
STEP 5
Draft aggregate operations
        ↓
STEP 6
Validation + freeze boundary
        ↓
STEP 7
Lifecycle service + audit
        ↓
STEP 8
Successor creation
        ↓
STEP 9
RBAC integration
        ↓
STEP 10
Declarative API/service surface
        ↓
STEP 11
Hydroponic/Thermal fixtures
        ↓
STEP 12
Invariant + negative tests
        ↓
STEP 13
Full regression
        ↓
STEP 14
Independent verification
```

---

# 39. Step 0 — Mandatory Repository Reconnaissance

Antes de escribir código se deberá identificar y documentar:

```text
current Alembic head
ORM conventions
ID type conventions
timestamp conventions
audit infrastructure
authorization/RBAC mechanism
API conventions
service-layer conventions
test layout
canonical JSON/hash utilities already present
repository module boundaries
```

También se deberá comprobar específicamente:

```text
migration 0007 control feature flag
control_engine_worker.py
first_order.py
DTE module boundaries
```

para garantizar que GDSS no invade esos subsistemas.

No se asumirán nombres, paths ni migraciones sin inspección.

---

# 40. Deliverables

GDSS-001 deberá producir como mínimo:

```text
implementation code
database migration
contracts/types
canonicalization implementation
hash implementation
lifecycle service
audit integration
RBAC integration
unit/dimension definitions
two domain fixtures
invariant tests
negative capability tests
dependency boundary test
documentation
verification report
```

---

# 41. Explicit Non-Deliverables

GDSS-001 no deberá entregar:

```text
simulation engine
ODE solver
Forrester engine
digital twin runtime
telemetry coupling
sensor ingestion
model calibration
counterfactual execution
recommendation engine
control integration
DTE integration
MQTT publishing
actuation
RL
MPC
ML inference
```

---

# 42. Implementation Gate

La aprobación de este plan autorizará únicamente la preparación del prompt operacional.

Secuencia:

```text
Architecture Package v0.2
        APPROVED
             ↓
Implementation Plan v0.1
        PROPOSED_FOR_REVIEW
             ↓
Human Review
             ↓
Implementation Plan
        APPROVED
             ↓
Operational Implementation Prompt
             ↓
Human Authorization
             ↓
Implementation
```

No deberá interpretarse la aprobación del plan como autorización implícita para modificar el repositorio.

---

# 43. Criterio de cierre

GDSS-001 podrá declararse completado únicamente cuando:

```text
contracts exist
persistence exists
versioning enforced
freeze boundary enforced
provenance preserved
units/dimensions validated
hash deterministic
lifecycle audited
RBAC enforced
domain neutrality demonstrated
operational dependencies absent
physical authority absent
invariants verified
baseline green
independent verification completed
```

---

# 44. Estado propuesto

```text
GDSS_STRATEGIC_DIRECTION
    APPROVED

GDSS-001_ARCHITECTURE_v0.2
    APPROVED

GDSS-001_IMPLEMENTATION_PLAN_v0.1
    PROPOSED_FOR_REVIEW

GDSS-001_IMPLEMENTATION
    NOT_YET_AUTHORIZED
```

---

# 45. Principio de aceptación final

> **GDSS-001 deberá demostrar que Midd-IoT puede representar, versionar, gobernar y auditar formalmente un sistema sin necesitar saber a qué dominio pertenece y sin adquirir por ello capacidad para ejecutarlo o actuar físicamente sobre él.**
