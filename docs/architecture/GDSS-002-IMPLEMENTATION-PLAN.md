# MIDD-IOT — GDSS-002
## Governed Safe Expression & Deterministic Evaluation Foundation
### Implementation Plan v0.1

**Version:** `v0.1`
**Status:** `PROPOSED_FOR_REVIEW`
**Implementation:** `NOT_YET_AUTHORIZED`
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Alembic baseline:** `0040`

## 1. Purpose

Este plan traduce el paquete arquitectónico GDSS-002 en pasos implementables sin inventar
semántica. La futura entrega interpretará fórmulas GDSS-001 mediante parser seguro, AST tipado,
resolución exacta, dimensiones, dependencias y evaluación pura.

```text
GOVERNED FORMULA → SAFE PARSER → TYPED AST → SYMBOL RESOLUTION
→ DIMENSIONAL VALIDATION → DEPENDENCY ANALYSIS
→ PURE DETERMINISTIC EVALUATION → DERIVED RESULT
```

No autoriza implementación, migración, commit ni push.

## 2. Baseline

- Checkout: `/Users/joseluis/dev/iot-midd-paas-auth-work`.
- Branch: `main`.
- HEAD: `295b521bb19eb77cba663d8df4b241a56f909e0c`.
- Alembic: `0040`, head único.
- Entrada documental: los cinco documentos `GDSS-002-*` de arquitectura, sin commit.
- Runtime objetivo futuro: TypeScript server-side en `apps/topology-next`, junto al core GDSS.

Antes de implementar se repetirá branch, HEAD, status, Alembic y checksum/estado de los documentos.
Cualquier divergencia no explicada activa el stop condition.

## 3. Scope

`GDSS_EXPR_V1`, tokenizer, parser recursivo, AST, diagnósticos, límites, resolver local, motor
dimensional, catálogo cerrado de conversiones, grafo/ciclos, evaluador puro, hashes derivados,
autorización de evaluación, fixtures neutrales y pruebas.

## 4. Non-scope

No se implementarán `SimulationRun`, tiempo, `dt`, estado previo/siguiente, ODE, integración,
Forrester/Stock-Flow, solver de loops, eventos, azar, calibración, predicción, contrafactuales,
Digital Shadow/Twin, MPC, RL, ML, telemetría, recomendación, política, MQTT ni actuación.

Ningún resultado crea `ControlPolicy`, `DeploymentAuthorization`, `DeploymentIntent`,
`ActuationAuthorization`, `ActuationIntent` o `ActuationCommand`, ni satisface una puerta M7.

## 5. Architectural dependencies

Sólo se permiten dependencias del núcleo futuro hacia tipos GDSS-001 y primitivas puras de
TypeScript/Node para SHA-256. El evaluador no importará DB, HTTP, repositories, services,
simulation, evaluation operacional, promotion, Control Engine, DTE, MQTT o actuación.

Fuente normativa: [ADR](GDSS-002-ADR.md), [contracts](GDSS-002-CONTRACTS.md),
[language](GDSS-002-EXPRESSION-LANGUAGE.md),
[dimensions](GDSS-002-DIMENSIONAL-SEMANTICS.md) e [invariants](GDSS-002-INVARIANTS.md).

## 6. CF-01 resolution

```text
GDSS2-CF-01 = RESOLVED_BY_NON_PERSISTENT_BINDING
```

`EvaluationInput` aportará `quantity_semantics: ABSOLUTE | INTERVAL` cuando la familia sea
affine; el contexto aportará la expectativa de salida. El binding es obligatorio, efímero,
hasheado y nunca inferido del símbolo de unidad. Su ausencia/contradicción falla con
`AFFINE_QUANTITY_ERROR`.

Pruebas obligatorias:

```text
20 °C ABSOLUTE → 293.15 K ABSOLUTE
Δ10 °C INTERVAL → Δ10 K INTERVAL
20 °C - 10 °C → Δ10 °C INTERVAL
20 °C + Δ10 °C → 30 °C ABSOLUTE
20 °C ABSOLUTE + 10 °C ABSOLUTE → reject
```

No se cambia ningún registro ni contrato persistido GDSS-001.

## 7. CF-02 resolution

```text
GDSS2-CF-02 = RESOLVED_WITHIN_GDSS_002
```

Se añadirá la operación lógica `evaluate`/capacidad `EVALUATE_MODEL` al chequeo GDSS existente,
sin tabla ni identidad nueva. Exigirá `oauth_session`, scope exacto de proyecto y rol de proyecto
`operator` o `admin`; `viewer`, fallback y fuera de scope fallan. Es un chequeo separado aunque
los mismos roles posean otras capacidades. Nunca llama a `transition`.

```text
EVALUATE_MODEL ≠ validate ≠ approve ≠ publish ≠ actuate
```

La superficie pura no conoce actores. Un adaptador server-side autoriza, obtiene un snapshot
exacto y recién entonces llama al pipeline sin pasarle capacidades.

## 8. CF-03 resolution

```text
GDSS2-CF-03 = RESOLVED_WITHIN_GDSS_002
```

Se implementará `UnitConversionCatalogVersion = GDSS_UNIT_CONVERSION_V1`, cerrado e inmutable en
código. Cada definición permitida se identifica por `(key, revision)` y declara dimensión,
scale, offset, unidad canónica versionada y quantity semantics admitidas. Una unidad del modelo
es evaluable sólo si su definición estructurada coincide exactamente con la entrada del catálogo.

El catálogo nunca ejecuta fórmulas de DB ni interpreta labels. Unidad desconocida, revisión o
tupla discordante, familia incompleta o target ambiguo produce `INVALID_INPUT_UNIT`. Añadir o
cambiar una definición requiere nueva versión de catálogo y, si altera cálculo, nueva
`EvaluatorVersion`. Modelos declarativamente válidos pueden ser no evaluables por unidad no
soportada.

No se requiere modificar persistencia GDSS-001.

## 9. Migration decision

```text
MIGRATION_DECISION = NO_MIGRATION_REQUIRED
```

AST, grafo, análisis, contextos y resultados son derivados o efímeros. Versiones de lenguaje,
evaluador y catálogo son definiciones inmutables en código. No se crea `0041`; DB debe permanecer
en `0040`. Persistencia/caché futura necesitará ADR, plan y autorización independientes.

## 10. Module design

Ubicación propuesta:

```text
apps/topology-next/src/lib/gdss/expression/
  versions.ts       identifiers immutable language/evaluator/catalog
  diagnostics.ts    codes, stages and builders
  limits.ts         profiles and counters
  tokens.ts         closed token union
  tokenizer.ts      source → tokens
  ast.ts            node contracts and canonical serialization
  parser.ts         recursive-descent GDSS_EXPR_V1 parser
  symbols.ts        exact version-local resolution
  dimensions.ts     seven-integer-vector algebra
  units.ts          catalog and explicit conversion
  dependencies.ts   graph, SCC and topological order
  canonical.ts      binary64/canonical hash encodings
  evaluator.ts      capability-free AST evaluator
  pipeline.ts       stage orchestration over immutable snapshots
  index.ts          narrow public exports

apps/topology-next/src/lib/services/gdss-evaluation.service.ts
  project authorization + exact read snapshot + pure pipeline call
```

No archivo monolítico mezclará parser, semántica y evaluación. `core.ts` conserva contratos
GDSS-001; sólo la operación de autorización estrictamente necesaria podrá añadirse a
`service.ts` o a una política GDSS dedicada.

## 11. Parser strategy

Decisión: parser dedicado recursive-descent, sin dependencia nueva. La gramática es pequeña y
cerrada; esta opción controla tokens, spans, AST, límites y determinismo, y evita supply-chain y
capacidades de evaluadores JavaScript generales. No se usará `eval`, `Function`, parser JS,
template engine ni librería que ejecute callbacks arbitrarios.

Stages: validar fuente/límite → tokenizar con spans → parsear por `additive`, `multiplicative`,
`unary`, `power`, `primary` → exigir EOF. Los contadores de recursos operan durante el proceso,
no después.

Tests: literales, notación científica, identifiers, unarios, binarios, paréntesis, calls,
malformados y tokens no soportados. Goldens obligatorios: `-2^2 = -(2^2)` y
`2^3^2 = 2^(3^2)`.

## 12. AST design

Union discriminada cerrada:

```text
NumericLiteral | SymbolReference | UnaryExpression
| BinaryExpression | FunctionCall
```

Cada nodo conserva span `[start,end)`; operandos/argumentos mantienen orden. No se simplifica ni
conmuta. Canonical AST usa JSON con claves ordenadas, arrays semánticos ordenados, lexeme numérico
canónico y versión. No incluye timestamps, IDs aleatorios ni mensajes humanos.

```text
same source + GDSS_EXPR_V1 → same canonical AST bytes
```

AST es `DERIVED`, `REGENERABLE`, no canónico respecto a GDSS-001.

## 13. Symbol resolution

`symbols.ts` construirá un mapa desde los hijos del `SystemModelVersion` exacto. Resolverá por
igualdad exacta de `symbol`; sólo Variable/Parameter. No label, alias, case folding, fuzzy match,
latest-version ni namespace global.

El set de símbolos AST debe coincidir con `input_refs` deduplicado. Fallos: `UNKNOWN_SYMBOL`,
`AMBIGUOUS_SYMBOL`, `CROSS_VERSION_REFERENCE`, `INVALID_SYMBOL_KIND` y
`DECLARED_DEPENDENCY_MISMATCH`. El adaptador nunca mezcla snapshots de versiones.

## 14. Formula output binding

Gate resuelto: la implementación real posee:

```text
expression_source = body
input_refs         = unordered governed dependency set
output_ref         = governed Variable/Parameter in same version
```

`validateContent` ya limita refs a cantidades y ownership local. GDSS-002 volverá a comprobarlo
en su frontera. No se añade asignación ni se requiere extensión GDSS-001.

## 15. Dependency analysis

El grafo se deriva de refs AST resueltas. Duplicados colapsan; nodes/edges se serializan por clave
estable. Se expondrán dependencias directas, transitivas y orden topológico si existe.

Se usará un algoritmo determinista de componentes fuertemente conexas con desempate léxico. SCC
de más de un nodo o self-loop produce `CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS`. No se
iterará, resolverá ni simulará el ciclo.

## 16. Dimensional engine

Funciones puras propuestas:

```text
assertKnownDimension
compatibleForAddSubtract
multiplyDimensions
divideDimensions
powerDimension
functionDimension
assertOutputDimension
```

Operan sólo sobre siete enteros. Suma/resta requiere igualdad; producto suma exponentes; división
resta; output debe coincidir. Vector cero es dimensionless; ausencia no. Overflow/límite de
exponente falla, sin rounding.

## 17. Unit and affine conversion

`units.ts` valida modelo contra `GDSS_UNIT_CONVERSION_V1`, normaliza a unidad canónica y convierte
a target explícito. Cada derivación registra source/target `(key,revision)`, catálogo, scale,
offset y quantity semantics.

Reglas affine siguen la matriz arquitectónica. Intervalos omiten offset; absolutos lo aplican.
Absolute+absolute, interval-absolute y multiplicación/división/potencia de absoluto affine fallan.
El resultado debe coincidir con el binding esperado de `output_ref`.

## 18. Evaluation context

Shape planeado:

```text
EvaluationContext {
  projectId, modelVersionId, formulaSymbol,
  expressionLanguageVersion, evaluatorVersion,
  conversionCatalogVersion, resourceLimitsProfile,
  inputs: Record<symbol, {
    value, unit: {key, revision}, quantitySemantics?
  }>,
  requestedOutputUnit?: {key, revision},
  expectedOutputQuantitySemantics?
}
```

Todos los valores, incluso `Parameter.default_value`, deben suministrarse explícitamente; no hay
default implícito. Inputs extras producen `UNDECLARED_INPUT`; faltantes, `MISSING_INPUT`. Ningún
campo permite recuperar datos.

## 19. Pure evaluator

`evaluator.ts` recibe AST validado, tabla resuelta ya normalizada y límites; no actor, DB client,
HTTP, MQTT, filesystem, environment, DTE, Control Engine ni actuator. Evalúa recursivamente en
orden AST, contando operaciones y comprobando finitud tras cada una.

No entrega resultado parcial. Éxito retorna `DERIVED`, `physical_authority: NONE`; fallo retorna
diagnósticos. La capa service sólo autoriza y obtiene snapshot read-only.

## 20. Numeric semantics

Binary64 normativo. Se rechazan literales/inputs/intermedios/resultados no finitos, divisor ±0,
sqrt negativo, log no positivo, potencia real inválida y overflow. `-0` se normaliza a `+0` al
ingreso de representaciones canónicas y al resultado.

Para hashes, cada número se codifica como los 8 bytes IEEE-754 big-endian expresados en hex tras
normalizar -0. No se confía en JSON decimal como identidad numérica. La operación sigue el orden
AST sin reordenamiento algebraico.

## 21. Resource limits

Perfil candidato inicial, sujeto a benchmark pero nunca a eliminación:

| Recurso | Candidato / techo |
|---|---:|
| source length | 2000 caracteres, techo GDSS-001 |
| token count | 1024 |
| AST depth | 64 |
| AST nodes | 1024 |
| distinct symbol references per formula | 256 |
| function nesting | 32 |
| dependency graph nodes | 1000, techo de hijos GDSS-001 |
| dependency graph edges | 10000 |
| supplied inputs | 256 |
| evaluator operations | 4096 |

Microbenchmarks con inputs de frontera medirán CPU/memoria en runtime oficial. Ajustes antes de
aceptación deben documentarse, mantenerse bajo techos del schema y conservar pruebas exact-at/
over-limit. Todo exceso es `RESOURCE_LIMIT_EXCEEDED`, sin salida parcial.

## 22. Diagnostics

Union de códigos estable con `code`, `stage`, `severity`, `formulaRef`, `sourceSpan`, `symbol`,
`expected`, `actual`, `message`. Tests afirman codes/campos, no sólo prosa. El pipeline puede
acumular errores seguros dentro de una etapa, pero nunca marca ni ejecuta etapas posteriores.

Stages normativos:

```text
SOURCE → PARSED → SYMBOL_RESOLVED → DIMENSIONALLY_VALIDATED → EVALUABLE
```

## 23. Security model

Defensa principal: ausencia de capacidades y gramática cerrada. Defensa secundaria: límites,
validación exacta, dispatch allowlisted y fail-closed. Amenazas a cubrir: code injection,
constructor/prototype traversal, property access, dynamic invocation, Unicode no soportado,
profundidad, tamaño, graph explosion, coerción, overflow y expresiones persistidas malformadas.

Un test AST/import boundary fallará si módulos puros importan paths prohibidos. Fuzzing acotado
verificará que cualquier entrada termina en AST válido o diagnóstico, nunca excepción sin tipar,
hang, I/O o ejecución arbitraria.

## 24. Authorization

El adaptador reutiliza `ControlActor`, `canAccessProject` y `getControlRoleForProject`. Sólo OAuth
scoped operator/admin obtiene `EVALUATE_MODEL`. No dev fallback. Se prueban viewer, operator,
admin, fuera de scope, proyecto sin membership y rol global que contradice rol de proyecto.

No se modifica `ControlPermissions` global salvo que el implementador demuestre que es el punto
canónico; la opción preferida es una política GDSS explícita para no reinterpretar permisos de
control. No requiere migración.

## 25. Lifecycle isolation

Se evaluarán DRAFT, VALIDATED, EXPERIMENTAL, APPROVED y PUBLISHED mediante snapshots; DEPRECATED
seguirá sujeto a lectura autorizada y también podrá reproducirse. Antes/después se compararán
contenido, hash, status, eventos y auditoría. Ninguna evaluación escribe o llama a transición.

```text
evaluation success ≠ VALIDATED ≠ APPROVED ≠ PUBLISHED
```

## 26. Hash and reproducibility strategy

Se implementarán tres SHA-256 derivados:

- `expression_ast_hash`: schema `gdss-expr-ast:v1`, language version + canonical AST;
- `evaluation_input_hash`: schema `gdss-eval-input:v1`, exact model/formula, all versions,
  limits profile, sorted inputs, units, bindings y binary64 bytes;
- `evaluation_result_hash`: schema `gdss-eval-result:v1`, input hash, output, derivation y status de
  éxito. Fallos no reciben result hash.

Son efímeros y separados de `SystemModelVersion.content_hash`. Parsear/evaluar debe dejar el hash
GDSS-001 byte-identical.

## 27. Domain-neutral fixtures

`tests/fixtures/gdss-expression.ts` tendrá modelos completos:

- hidropónico: `cross_section_area * fluid_velocity → flow_rate`;
- térmico: `thermal_transmittance * area * temperature_difference → heat_loss`.

Ambos usan la misma API y catálogo. Vocabulario de dominio queda sólo en fixtures. Un test AST de
sources del core prohibirá tokens de ambos dominios.

## 28. Invariant-to-test matrix

Todos permanecen `NOT_TESTED` hasta ejecución real.

| Invariant | Planned test/location | Positive case | Negative case | Enforcement |
|---|---|---|---|---|
| GDS2-INV-01 | unit `gdss-expression.security.test.ts` | arithmetic allowlist | eval/constructor/property payloads | tokenizer/parser/evaluator |
| GDS2-INV-02 | integration `gdss.evaluation.integration.test.ts` | owned formula | raw/unowned text | evaluation service |
| GDS2-INV-03 | unit `gdss-expression.pipeline.test.ts` | known versions | missing/unknown version | versions/pipeline |
| GDS2-INV-04 | unit `gdss-expression.symbols.test.ts` | exact unique symbol | unknown/ambiguous | resolver |
| GDS2-INV-05 | integration | same-version refs | cross-version same name | snapshot/resolver |
| GDS2-INV-06 | unit `gdss-expression.dimensions.test.ts` | compatible operations | m+s/output mismatch | dimensional engine |
| GDS2-INV-07 | unit `gdss-expression.units.test.ts` | m↔cm conversion | same dimension unsupported unit | catalog |
| GDS2-INV-08 | unit dimensions | zero vector | absent/malformed dimension | decoder |
| GDS2-INV-09 | unit units | five mandated affine cases | missing/invalid binding | affine rules |
| GDS2-INV-10 | unit `gdss-expression.dependencies.test.ts` | dependency edge | causal field absent/rejected | graph contract |
| GDS2-INV-11 | unit dependencies | DAG topological order | self/multi-node cycle diagnostic | SCC analyzer |
| GDS2-INV-12 | unit pipeline | complete context | valid + missing input | staged pipeline |
| GDS2-INV-13 | unit evaluator | exact supplied map | missing/extra/implicit default | context validator |
| GDS2-INV-14 | unit security | pure execution | forbidden imports/I/O probes | capability boundary |
| GDS2-INV-15 | unit evaluator | result `DERIVED` | alternate epistemic class rejected | result builder |
| GDS2-INV-16 | unit contracts | computational status | scientific claim fields rejected | closed result schema |
| GDS2-INV-17 | integration | every lifecycle evaluates | model/event/audit mutation | read-only service |
| GDS2-INV-18 | unit/integration auth | operator/admin evaluate | viewer/publisher implication | GDSS auth policy |
| GDS2-INV-19 | unit security | authority NONE | actuation types/import/path | result/boundary |
| GDS2-INV-20 | unit source boundary | allowed imports | Control/DTE/MQTT imports | AST import inspection |
| GDS2-INV-21 | integration | parse/evaluate | content hash before/after differs | derived hash layer |
| GDS2-INV-22 | unit golden vectors | repeated/cross-process bytes | version/input change | canonical/evaluator |
| GDS2-INV-23 | unit parser | allowlisted ops/functions | unknown op/function | parser dispatch |
| GDS2-INV-24 | unit `gdss-expression.limits.test.ts` | exact limit | each limit +1 | counters |
| GDS2-INV-25 | unit fixtures/source | hydroponic + thermal | domain term in core | shared pipeline |

## 29. Negative capability tests

Tests estructurales inspeccionarán imports y superficie pública; dobles de entorno harán fallar si
se intenta acceder a network, filesystem, environment, DB, HTTP, MQTT, Control Engine, DTE,
telemetría o actuación. Casos adversariales incluyen constructor/prototype traversal, `.`, `[]`,
dynamic call, Unicode inválido, paréntesis/nesting/tamaño extremos, explosion de grafo, `1/0`,
`0/0`, overflow, `sqrt(-1)`, `ln(0)`, `ln(-1)`, exponentes malformados y función desconocida.

No se alegará seguridad sólo por mocks: import graph y contratos deben demostrar ausencia de la
capacidad.

## 30. Regression plan

Gates futuros, en orden:

1. tests unitarios GDSS-002 y goldens/fuzz acotado;
2. integración read-only/autorización si se añade adaptador con DB;
3. suite GDSS-001 (13 unit + 12 PostgreSQL de referencia);
4. regresión completa relevante Next con runners establecidos;
5. `npm run typecheck`;
6. production build;
7. Python regression para asegurar frontera sin acoplamiento;
8. `git diff --check` incluyendo archivos nuevos staged o equivalente;
9. Alembic code/DB `0040`, head único;
10. conteos de residuos: cero modelos/resultados creados por evaluación.

## 31. Implementation sequence

```text
Step 0  baseline, architecture and working-tree classification
Step 1  encode CF-01 ephemeral binding contracts/tests
Step 2  encode CF-02 authorization policy/tests
Step 3  encode CF-03 closed catalog/tests
Step 4  diagnostics, versions, limits and canonical binary64
Step 5  tokenizer
Step 6  parser + typed AST + AST canonicalization
Step 7  exact symbol resolver + declared-ref reconciliation
Step 8  dimensional engine
Step 9  unit/affine conversion
Step 10 deterministic dependency graph + cycles
Step 11 pure evaluator + staged pipeline
Step 12 derived hashes
Step 13 neutral fixtures
Step 14 invariant/security/adversarial tests
Step 15 complete regression and boundary verification
Step 16 final implementation report
```

Steps 4+ no avanzan si CF-01..03 dejan de sostener su resolución durante implementación.

## 32. Stop conditions

Detener y clasificar `REQUIRES_GDSS_001_CONTRACT_EXTENSION` si hace falta reinterpretar registros,
persistir quantity semantics, cambiar firma dimensional o modificar ownership/output. Detener si
el catálogo no puede ser reproducible, RBAC debilita scope, se requiere código general o surge
acoplamiento a Control Engine/DTE/MQTT/actuación. No improvisar migración, fallback ni solver.

## 33. Acceptance criteria

La implementación futura sólo cierra si demuestra:

- parsing/AST determinista y precedencia aprobada;
- cero arbitrary code y funciones/operators fail-closed;
- resolución exacta y version-local;
- dimensionalidad, affine y conversiones reproducibles;
- ciclos diagnosticados sin simulación;
- inputs explícitos, pureza y límites;
- fallos numéricos estructurados;
- resultados `DERIVED`, lifecycle/content hash sin cambios;
- invariantes GDS2-INV-01..25 con evidencia real;
- Control Engine, DTE, MQTT, simulation, telemetry y physical actuation: `NONE`;
- typecheck, build y regresiones verdes;
- Alembic `0040`, sin `0041`.

## 34. Final reporting requirements

El informe futuro incluirá baseline y diff atribuible; disposiciones CF; decisión de migración;
módulos; versiones; límites finales y benchmarks; matriz 25/25 con evidencia; resultados de tests,
typecheck/build/Python/Alembic; residuos; fronteras `NONE`; hashes; hallazgos; Git y push status.

Completar este plan no autoriza esas acciones. La secuencia permanece:

```text
Architecture approval → Plan review/approval → Operational prompt → Implementation
```

> **Executable mathematics does not confer executable physical authority.**
