> Architecture Package v0.2 — Estado: `APPROVED`.
> Clase estratégica: A1 — Digital Twin Foundation. R1 resolvió el baseline: `STEP_0_GATE = PASS`. Implementación completada con advertencias no bloqueantes; véase el [informe final](GDSS-001-FINAL-REPORT.md).
> Este documento especifica requisitos arquitectónicos aprobados; no describe capacidades GDSS implementadas.

> Los estados `ENFORCED`, `ENFORCED_PARTIAL` y `ENFORCED_SEMANTICALLY` de esta matriz conservan la cobertura exigida originalmente. La cobertura efectiva, sus límites y las pruebas de cada uno de los 22 invariantes están documentados en el [informe final](GDSS-001-FINAL-REPORT.md); no debe confundirse el requisito con la evidencia.

## Matriz canónica inicial

| ID | Invariante | Estado GDSS-001 | Enforcement |
|---|---|---|---|
| GDS-INV-01 | SIMULATED ≠ OBSERVED | ENFORCED | epistemic kinds separados |
| GDS-INV-02 | PREDICTED ≠ MEASURED | ENFORCED | categorías distintas |
| GDS-INV-03 | FORMULA ≠ RULE ≠ POLICY | ENFORCED | contratos/namespaces independientes |
| GDS-INV-04 | MODEL ≠ SIMULATION_RUN ≠ DIGITAL_TWIN | ENFORCED | sólo Model existe en 001 |
| GDS-INV-05 | Simulation has zero physical authority | ENFORCED | ausencia + dependency tests |
| GDS-INV-06 | Every SystemModel is explicitly versioned; every governed child is historically versioned by membership in exactly one SystemModelVersion | ENFORCED | aggregate versionado, pertenencia exclusiva y contenido congelado desde VALIDATED |
| GDS-INV-07 | Every result identifies exact model version | STRUCTURALLY_RESERVED | no results en 001 |
| GDS-INV-08 | Published runs are reproducible | STRUCTURALLY_RESERVED | no SimulationRun |
| GDS-INV-09 | Units/dimensions are validated | ENFORCED_PARTIAL | catálogo + compatibilidad declarativa |
| GDS-INV-10 | Model provenance is preserved | ENFORCED | provenance obligatorio |
| GDS-INV-11 | AI_PROPOSED ≠ SCIENTIFICALLY_VALIDATED | ENFORCED | provenance + lifecycle separados |
| GDS-INV-12 | Experimental cannot silently become operational | ENFORCED | no operational bridge |
| GDS-INV-13 | Physical binding requires governance | STRUCTURALLY_RESERVED | binding inexistente |
| GDS-INV-14 | Composition cannot erase provenance | ENFORCED | preservation / aggregation without epistemic promotion |
| GDS-INV-15 | Historical simulation results immutable | STRUCTURALLY_RESERVED | no results todavía |
| GDS-INV-16 | Domain packages do not define core semantics | ENFORCED | architecture/vocabulary tests |
| GDS-INV-17 | Model changes do not alter historical runs | STRUCTURALLY_RESERVED | runtime futuro |
| GDS-INV-18 | COUNTERFACTUAL ≠ OBSERVED HISTORY | ENFORCED_SEMANTICALLY | tipos reservados separados |
| GDS-INV-19 | CALIBRATED ≠ UNIVERSALLY_VALID | ENFORCED | provenance/validity domain |
| GDS-INV-20 | Digital Twin requires physical binding | STRUCTURALLY_RESERVED | twin fuera de alcance |
| GDS-INV-21 | VALIDATED ≠ SCIENTIFICALLY_VALIDATED | ENFORCED | validación estructural y de gobernanza sin acreditación científica |
| GDS-INV-22 | COMPUTATIONAL_ROLE ≠ EPISTEMIC_KIND | ENFORCED | campos independientes, sin inferencia automática |

Evolución v0.2: se conservan GDS-INV-01..20 y se reformula GDS-INV-06 por R1/R2. GDS-INV-21 y GDS-INV-22 se incorporan explícitamente por R4 y R3 de Architectural Review v0.1. Todos los mecanismos y tests aquí descritos son requisitos futuros; enforcement de implementación: `NOT TESTED`.

GDS-INV-06: cada hijo pertenece históricamente a una versión exacta. Su contenido es editable sólo mientras esa versión está en `DRAFT`; desde `VALIDATED` la pertenencia y el contenido quedan congelados. Ninguna mutación de un hijo o sucesor puede alterar el contenido histórico de otra versión. No se exige un lifecycle o versionado independiente de `Formula`.

GDS-INV-21: `VALIDATED` significa que el artefacto superó las validaciones estructurales y de gobernanza exigibles a GDSS-001. No implica validación científica, empírica, predictiva ni operacional; tampoco cambia procedencia. `VALIDATED ≠ EMPIRICALLY_CONFIRMED` y `VALIDATED ≠ OPERATIONALLY_SAFE`.

---

# 1. Tests obligatorios de neutralidad

Se crearán dos fixtures.

## Fixture A — Hydroponic

Podrá utilizar conceptos de dominio tales como:

```text
nutrient_solution
water_temperature
electrical_conductivity
```

pero exclusivamente dentro del fixture.

---

## Fixture B — Thermal

Podrá contener:

```text
room
internal_temperature
external_temperature
thermal_resistance
```

Ninguno de esos términos podrá ser requerido por el core.

---

# 2. Test de vocabulario

Deberá existir una prueba automatizada que falle si los contratos del core incorporan vocabulario prohibido de fixtures.

Conjunto inicial indicativo:

```text
hydroponic
nutrient
lettuce
plant
greenhouse
room
HVAC
heater
```

El mecanismo deberá evitar falsos positivos en documentación/tests donde dichos términos sean legítimos.

---

# 3. Dependency boundary test

El core deberá fallar CI si importa directamente módulos pertenecientes a:

```text
parametric-control-engine
DTE
MQTT publishing
deployment execution
runtime physical binding
physical actuation
```

---

# 4. Lifecycle tests

Deberán verificarse:

```text
DRAFT → VALIDATED               PASS
VALIDATED → EXPERIMENTAL        PASS
EXPERIMENTAL → APPROVED         PASS
APPROVED → PUBLISHED            PASS
PUBLISHED → DEPRECATED          PASS
```

y transiciones ilegales:

```text
DRAFT → PUBLISHED               REJECT
DRAFT → APPROVED                REJECT
PUBLISHED → DRAFT               REJECT
DEPRECATED → PUBLISHED          REJECT
```

salvo futura decisión explícita de gobernanza que cree una nueva versión.

El lifecycle se prueba exclusivamente sobre `SystemModelVersion`. Los hijos no tienen transiciones independientes. Crear un sucesor `DRAFT` deja intacto el estado del predecesor. Validar debe congelar exactamente el contenido comprobado y registrar actor, razón, estado anterior y nuevo estado.

---

# 5. Immutability tests

Para cada estado `VALIDATED`, `EXPERIMENTAL`, `APPROVED`, `PUBLISHED` y `DEPRECATED`:

```text
change formula       REJECT
change parameter     REJECT
change component     REJECT
change provenance    REJECT
change constraint    REJECT
change variable      REJECT
change boundary      REJECT
```

La operación correcta será:

```text
CREATE NEW DRAFT SUCCESSOR VERSION
```

En `DRAFT`, una edición autorizada debe ser aceptada. El sucesor debe poder editarse sin cambiar hijos ni hash del original. `PUBLISHED → DEPRECATED` debe preservar contenido y hash y agregar un evento. Las referencias entre hijos de versiones diferentes deberán rechazarse para los seis tipos de hijos; una referencia a la propia versión deberá aceptarse.

---

# 6. Hash determinism

Dos representaciones semánticamente idénticas deberán producir el mismo `content_hash` independientemente de:

- orden no semántico;
- UUID;
- timestamp;
- serialización incidental.

Un cambio semántico deberá modificar el hash.

NB-01: reordenar una colección declarada sin orden debe preservar el hash; reordenar una secuencia declarada con orden semántico debe cambiarlo. La clasificación por campo se fijará en el plan. Cambiar sólo el lifecycle no modifica el hash del contenido congelado.

---

# 7. Provenance tests

La procedencia deberá:

- ser obligatoria donde corresponda;
- sobrevivir al versionado;
- sobrevivir a la composición;
- no elevarse automáticamente;
- no convertirse de `AI_PROPOSED` a `LITERATURE`;
- no convertirse de `CALIBRATED` a universal.

GDS-INV-21: validar un modelo `AI_PROPOSED` debe conservar esa procedencia y no crear acreditación científica. NB-03: una composición de elementos `LITERATURE`, `EMPIRICAL` y `AI_PROPOSED` deberá mantener las tres procedencias identificables.

GDS-INV-22: los contratos deberán conservar `computational_role` y `epistemic_kind` por separado, rechazar valores fuera de cada taxonomía y no inferir uno a partir del otro. Declarar `INPUT/OBSERVED` o `OUTPUT/SIMULATED` no debe conferir ninguna capacidad de ejecución.

---

# 8. Unit tests

GDSS-001 deberá poder determinar al menos:

```text
m compatible m       PASS
°C compatible K      DIMENSIONALLY_COMPATIBLE
m incompatible s     REJECT
Pa incompatible kg   REJECT
```

Las conversiones y operaciones algebraicas complejas quedan para GDSS-002 cuando exista parser seguro.

---

# 9. Tests negativos de autoridad física

No deberá ser posible construir mediante contratos GDSS-001:

```text
publish MQTT
open valve
start pump
deploy policy
authorize actuation
execute command
```

No basta con que estas operaciones no se usen.

**No deben formar parte de la superficie funcional GDSS-001.**

---

# 10. Definition of Done

GDSS-001 podrá considerarse cerrado únicamente cuando:

1. existan contratos neutrales de dominio;
2. identidad y versión estén separadas;
3. sólo `DRAFT` permita edición autorizada y el contenido sea inmutable desde `VALIDATED`;
4. lifecycle sea explícito y auditado;
5. procedencia sea obligatoria y preservada;
6. unidades/dimensiones dispongan de contrato canónico;
7. fixtures hidropónico y térmico utilicen exactamente el mismo core;
8. tests demuestren independencia de dominio;
9. tests demuestren ausencia de dependencias operacionales;
10. no exista motor de simulación;
11. no exista integración DTE;
12. no exista integración Control Engine;
13. no exista telemetría acoplada;
14. no exista recomendación operacional;
15. no exista actuación física;
16. los invariantes `ENFORCED` estén automatizados;
17. los `STRUCTURALLY_RESERVED` estén documentados sin implementaciones ficticias;
18. build y tests previos permanezcan verdes.

---

# CRITERIO DE ACEPTACIÓN ARQUITECTÓNICO

La prueba definitiva de GDSS-001 será:

> **Eliminar ambos fixtures de demostración debe dejar un núcleo completamente funcional y semánticamente coherente que no revele si fue diseñado pensando en hidroponía, climatización, energía, industria o cualquier otro dominio.**

Y simultáneamente:

> **Instalar cualquiera de esos dominios no debe conferir al modelo ninguna capacidad operacional o física.**

---

# ESTADO PROPUESTO

```text
GDSS_STRATEGIC_DIRECTION
        APPROVED

GDSS-001_ARCHITECTURE_v0.1
        APPROVED_WITH_REQUIRED_REMEDIATIONS

GDSS-001_ARCHITECTURE_v0.2
        APPROVED

R1–R5
        DOCUMENTALLY_ADDRESSED_IN_APPROVED_v0.2

GDSS-001_IMPLEMENTATION_PLAN_v0.1
        APPROVED

IMPLEMENTATION
        COMPLETED_GOVERNED_DECLARATIVE_SYSTEMS_FOUNDATION_WITH_WARNINGS
```

## Próxima puerta

El mandato [MIDD-GDSS-P001](GDSS-001-OPERATIONAL-PROMPT.md) declara aprobado el plan y ordena ejecución. R1 resolvió el baseline documentado en el [informe STEP 0 histórico](GDSS-001-STEP-0-REPORT.md). La ejecución está cerrada según el [informe final](GDSS-001-FINAL-REPORT.md), que explicita el alcance de la verificación y no afirma una revisión externa independiente. Se conserva abajo la secuencia de autorización como referencia histórica:

```text
IMPLEMENTATION PLAN v0.1 — HUMAN REVIEW
          ↓
IMPLEMENTATION PLAN APPROVED
          ↓
OPERATIONAL IMPLEMENTATION PROMPT
          ↓
HUMAN AUTHORIZATION
          ↓
IMPLEMENTATION
          ↓
INDEPENDENT VERIFICATION
```

No deberá saltarse directamente desde este ADR a implementación.
