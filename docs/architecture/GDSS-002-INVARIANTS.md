# MIDD-IOT — GDSS-002
## Invariants v0.1

**Status:** `PROPOSED_FOR_REVIEW`
**Phase:** `GDSS-002`
**Canonical name:** Governed Safe Expression & Deterministic Evaluation Foundation
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Implementation:** `NOT_YET_AUTHORIZED`

La matriz describe obligaciones propuestas, no evidencia ejecutada. Todo invariant dependiente de
implementación está `NOT_TESTED`. Ninguno se declara `PASS` por estar documentado.

| ID | Statement | Rationale | Planned enforcement layer | Planned verification | Pre-implementation status |
|---|---|---|---|---|---|
| GDS2-INV-01 | No arbitrary code execution. | El texto gobernado no es código general. | tokenizer, grammar, typed evaluator, capability absence | payloads de inyección, AST/import inspection, negative fuzzing | NOT_TESTED |
| GDS2-INV-02 | Every executable expression originates from a governed formula. | Evita expresiones ad hoc sin ownership. | evaluation boundary bound to exact model/formula | reject raw/unowned expression; ownership tests | NOT_TESTED |
| GDS2-INV-03 | Expression language/parser version is explicit. | Hace reproducible la interpretación. | `ParsedExpression` and context contracts | missing/unknown/version-change tests | NOT_TESTED |
| GDS2-INV-04 | Unknown or ambiguous symbols fail closed. | No se adivina significado. | resolver with exact cardinality | zero/multiple candidate fixtures | NOT_TESTED |
| GDS2-INV-05 | Symbol resolution cannot escape the exact `SystemModelVersion`. | Preserva ownership histórico. | version-scoped symbol table | cross-version and same-name tests | NOT_TESTED |
| GDS2-INV-06 | Dimensional incompatibility fails validation. | Impide matemática incoherente. | dimensional validator before evaluator | operator/function/output mismatch matrix | NOT_TESTED |
| GDS2-INV-07 | Unit identity ≠ dimensional compatibility. | Igual dimensión aún requiere conversión. | exact unit revision plus conversion engine | m/cm and K/°C cases | NOT_TESTED |
| GDS2-INV-08 | Missing dimension ≠ dimensionless. | Ausencia no equivale a vector cero. | signature decoder and resolver | missing/malformed versus zero-vector cases | NOT_TESTED |
| GDS2-INV-09 | Affine conversion semantics are explicit. | Offset exige distinguir absoluto/intervalo. | quantity-kind binding and affine rules | full affine operation table | NOT_TESTED |
| GDS2-INV-10 | Computational dependency ≠ causal relation. | Referencia matemática no prueba causalidad. | graph contract excludes causal fields | contract/schema and vocabulary inspection | NOT_TESTED |
| GDS2-INV-11 | Dependency cycle ≠ automatically invalid scientific model. | Feedback puede requerir dinámica futura. | SCC diagnostic, no scientific rejection | self/multi-node cycle tests | NOT_TESTED |
| GDS2-INV-12 | Valid expression ≠ currently evaluable expression. | Puede faltar un valor explícito. | distinct validation/evaluability status | missing-input cases remain computationally valid | NOT_TESTED |
| GDS2-INV-13 | Evaluation uses only explicit inputs. | Reproducibilidad y aislamiento. | closed `EvaluationContext` | undeclared/missing/implicit lookup tests | NOT_TESTED |
| GDS2-INV-14 | Evaluation performs no external I/O. | Una función pura no observa el mundo. | evaluator has no I/O clients or imports | dependency inspection and denied-I/O harness | NOT_TESTED |
| GDS2-INV-15 | Evaluation result is `DERIVED`. | Cálculo no es observación. | constant result epistemic classification | result contract assertions | NOT_TESTED |
| GDS2-INV-16 | Computational validity ≠ scientific validity. | Ejecutar no demuestra verdad. | no scientific-validity state/output | closed-schema and lifecycle tests | NOT_TESTED |
| GDS2-INV-17 | Successful evaluation cannot alter lifecycle. | Lifecycle continúa humano y gobernado. | pure evaluator, mutation-free service boundary | before/after model and audit snapshots | NOT_TESTED |
| GDS2-INV-18 | Evaluation authority ≠ publication authority. | Separa usos computacionales y gobernanza. | project RBAC operation separation | role matrix tests | NOT_TESTED |
| GDS2-INV-19 | Evaluation result confers zero physical authority. | Resultado no es autorización/comando. | result contract `physical_authority: NONE`; no routes to actuation | dependency/contract tests and negative integration | NOT_TESTED |
| GDS2-INV-20 | No dependency on Control Engine, DTE, MQTT or actuation. | Mantiene frontera A1 neutral. | module/dependency boundary | import graph and forbidden vocabulary tests | NOT_TESTED |
| GDS2-INV-21 | Derived AST/graph does not alter GDSS-001 `content_hash`. | Preserva identidad declarativa. | separate derived hashes, read-only model | hash snapshot before/after parse/evaluate | NOT_TESTED |
| GDS2-INV-22 | Same governed expression + versions + explicit inputs produces deterministic result under defined numeric semantics. | Base de reproducibilidad. | fixed AST order, binary64 policy, versioned evaluator | repeated/cross-process golden vectors | NOT_TESTED |
| GDS2-INV-23 | Unsupported functions/operators fail closed. | La allowlist es la autoridad. | lexer/parser/function dispatch | exhaustive negative grammar cases | NOT_TESTED |
| GDS2-INV-24 | Evaluation resource limits are enforced. | Previene agotamiento y explosión. | bounded tokenizer/parser/graph/evaluator | boundary, over-limit and fuzz tests | NOT_TESTED |
| GDS2-INV-25 | Domain fixtures use the same neutral computational core. | El dominio conoce al engine, no al revés. | single parser/resolver/evaluator API | hydroponic and thermal fixtures plus source inspection | NOT_TESTED |

## 1. Semántica normativa adicional

### GDS2-INV-01 y GDS2-INV-14

No basta con bloquear llamadas por nombre. El núcleo futuro carecerá de referencias a APIs de
red, filesystem, proceso, SQL, entorno, MQTT, DTE, Control Engine y actuación. El AST sólo puede
expresar nodos cerrados y el dispatch de función sólo puede seleccionar implementaciones puras
pre-registradas.

### GDS2-INV-02 y GDS2-INV-05

La tupla de ownership es:

```text
project_id + model_version_id + formula_symbol
```

El texto por sí solo no es evaluable mediante la superficie gobernada. Copiar el mismo texto a
otra versión crea otra procedencia computacional aunque derive el mismo AST.

### GDS2-INV-09

Mientras GDSS-001 no codifique `ABSOLUTE | INTERVAL`, toda evaluación affine requiere binding
explícito incluido en el contexto reproducible. Ausencia o contradicción falla; no se infiere.

### GDS2-INV-11

Un ciclo impide el orden topológico requerido para evaluación algebraica ordinaria y produce
`CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS`. No cambia lifecycle ni validez científica. No se
implementa iteración ni solver.

### GDS2-INV-12

`VALID_BUT_MISSING_INPUTS` conserva el éxito de parsing, resolución y dimensión y falla sólo la
etapa `EVALUABLE`. No genera resultado numérico parcial.

### GDS2-INV-19

Está prohibida toda conversión directa o indirecta:

```text
ExpressionEvaluationResult ─X→ ActuationAuthorization
ExpressionEvaluationResult ─X→ ActuationCommand
```

Una fase posterior sólo podrá tratar el resultado como evidencia a través de gobernanza explícita.

### GDS2-INV-22

La garantía está acotada por `ExpressionLanguageVersion`, `EvaluatorVersion`, modelo exacto,
fórmula, unidades, quantity kinds, inputs y perfil semántico. No promete igualdad entre versiones
distintas ni entre hardware/runtimes que incumplan la especificación binary64 documentada.

## 2. Diagnósticos de verificación obligatorios

La futura suite deberá probar al menos:

- precedencia `-2^2`, asociación `2^3^2` y funciones allowlisted;
- NaN, infinitos, cero divisor, overflow y dominios inválidos;
- referencias desconocidas, ambiguas, cruzadas, de clase inválida y no declaradas;
- igualdad dimensional con conversión de unidad y mismatch;
- matriz completa de cantidades affine;
- DAG determinista, refs duplicadas y ciclos;
- límites exactamente en y sobre cada frontera;
- hashes GDSS-001 inmutables;
- misma superficie para los dos dominios;
- ausencia de side effects, lifecycle, publicación y autoridad física.

## 3. Invariantes estructuralmente reservados

Ninguno de GDS2-INV-01..25 se clasifica aquí como `STRUCTURALLY_RESERVED`: todos son obligaciones
de la futura implementación GDSS-002 y por eso están `NOT_TESTED`. Simulación, predicción,
recomendación y actuación sí son conceptos futuros fuera de esta matriz; su ausencia es una
frontera, no un supuesto PASS.
