# MIDD-IOT — GDSS-002
## Architecture Decision Record v0.1

**Status:** `PROPOSED_FOR_REVIEW`
**Phase:** `GDSS-002`
**Canonical name:** Governed Safe Expression & Deterministic Evaluation Foundation
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Implementation:** `NOT_YET_AUTHORIZED`

## 1. Decision

GDSS-002 propone interpretar únicamente el `expression_source` de una `Formula` perteneciente a
un `SystemModelVersion` exacto mediante una cadena sin capacidades externas:

```text
Tokenizer → Parser → Typed AST → Symbol Resolver
          → Dimensional Validator → Dependency Analyzer → Pure Evaluator
```

La implementación futura será un núcleo matemático neutral, puro y acotado. No adaptará un
runtime de propósito general ni recibirá clientes de base de datos, red, filesystem, MQTT,
Control Engine, DTE o actuación.

```text
DECLARATION ≠ PARSED REPRESENTATION ≠ VALIDATION ≠ EVALUATION
            ≠ SIMULATION ≠ PREDICTION ≠ RECOMMENDATION
            ≠ AUTHORIZATION ≠ ACTUATION
```

## 2. Alcance

Incluye lenguaje `GDSS_EXPR_V1`, AST tipado, resolución local, álgebra dimensional, conversión
explícita de unidades, grafo de dependencias, detección de ciclos, evaluación determinista con
entradas explícitas y diagnósticos estructurados.

No incluye eje temporal, estado previo, integración, solver ODE/algebraico, scheduler, azar,
feedback runtime, `SimulationRun`, telemetría, inferencia causal, recomendación, política,
control ni actuación. Un DAG algebraico puede evaluarse; un ciclo sólo puede diagnosticarse.

## 3. Fuente y salida de una fórmula

- El texto exacto a parsear es `Formula.expression_source`, sin prefijo de asignación.
- La salida es el `Formula.output_ref` ya gobernado por GDSS-001.
- `input_refs` es la declaración autorizada de dependencias esperadas. Los símbolos observados
  en el AST deben coincidir exactamente con su conjunto normalizado; cualquier diferencia falla.
- `output_ref` e `input_refs` resuelven por `Child.symbol`, no por `label`, nombre mostrado ni
  aproximación textual, y sólo dentro del mismo `SystemModelVersion`.
- Sólo `Variable` y `Parameter` son cantidades resolubles en v1, conforme a GDSS-001.

Esto evita introducir asignación en el lenguaje y confirma que no existe incompatibilidad de
salida. La unicidad `(model_version_id, symbol)` de GDSS-001 elimina ambigüedad en contenido
válido; el resolver conserva `AMBIGUOUS_SYMBOL` para entradas derivadas corruptas o no canónicas.

## 4. Lenguaje y seguridad

Se adopta un tokenizer y parser dedicados para la gramática cerrada de
[GDSS_EXPR_V1](GDSS-002-EXPRESSION-LANGUAGE.md). Están prohibidos `eval`, `Function`, import
dinámico, shell, subprocess, SQL, reflexión, callbacks, acceso a propiedades, red, filesystem,
variables de entorno y coerción implícita. Un nombre de función sólo es invocable si pertenece a
la allowlist versionada.

La arquitectura reduce capacidades por construcción: el evaluador recibe AST validado,
símbolos resueltos y valores; nunca recibe servicios externos. Entradas persistidas malformadas
atraviesan de nuevo todas las etapas y fallan cerradas.

## 5. Semántica numérica

`GDSS_EXPR_V1` adopta IEEE-754 binary64 con estas reglas normativas:

- sólo valores finitos entran o salen;
- `NaN`, `+Infinity` y `-Infinity` se rechazan;
- división por `+0` o `-0` falla con `DIVISION_BY_ZERO`;
- todo intermedio se comprueba inmediatamente y un valor no finito falla;
- dominios inválidos de raíz, logaritmo o potencia fallan, sin números complejos;
- no hay redondeo implícito distinto del propio binary64; conversiones y operaciones siguen un
  orden AST definido, sin reordenamiento algebraico;
- `-0` se normaliza a `+0` en el resultado y en hashes derivados;
- la serialización reproducible usa una representación canónica de binary64 definida por el
  futuro plan y versionada por `EvaluatorVersion`.

Determinismo significa mismo modelo, fórmula, versiones, bindings e inputs sobre una
implementación conforme, no identidad bit a bit entre versiones de evaluador distintas. Toda
modificación de reglas requiere nueva `ExpressionLanguageVersion` o `EvaluatorVersion`.

## 6. Artefactos y hashing

| Artefacto | Clase | Mutabilidad / autoridad |
|---|---|---|
| `Formula.expression_source`, refs y salida | CANONICAL, GDSS-001 | siguen lifecycle y `content_hash` de la versión |
| Definición `GDSS_EXPR_V1` | VERSIONED DEFINITION | inmutable por identificador |
| AST, grafo y análisis dimensional | DERIVED / REGENERABLE | sin autoridad y regenerables |
| Contexto y resultado | EPHEMERAL | no persistidos en GDSS-002 |

El `content_hash` de GDSS-001 no cambia. Si la implementación necesita identidad reproducible,
usará hashes separados (`expression_ast_hash`, `evaluation_input_hash`,
`evaluation_result_hash`) con esquema y versión explícitos. Ninguno sustituye ni retroalimenta el
hash declarativo.

No se presume migración. Cualquier caché o persistencia futura requiere justificación y mandato
separados; el cache, si existiera, sería descartable y verificable contra sus derivaciones.

## 7. Dimensiones y unidades

La firma sigue el vector entero de siete bases SI de GDSS-001. El validador aplica las reglas de
[semántica dimensional](GDSS-002-DIMENSIONAL-SEMANTICS.md). Igual dimensión no implica igual
unidad ni intercambio numérico. Todo input declara unidad y se normaliza explícitamente; la
salida se convierte de manera explícita a la unidad gobernada de `output_ref`.

`[0,0,0,0,0,0,0]` es dimensión conocida y adimensional. Una dimensión ausente o desconocida es
un error, no ese vector.

## 8. Compatibilidad affine

**ARCHITECTURAL_COMPATIBILITY_FINDING GDSS2-CF-01:** GDSS-001 representa `scale`, `offset` y
`canonical_unit`, pero no clasifica un símbolo como cantidad `ABSOLUTE` o `INTERVAL`. Esa
distinción no puede inferirse de la dimensión ni del hecho de que una unidad tenga offset.

Estrategia segura de GDSS-002:

1. no se modifica el contrato histórico;
2. cada evaluación que involucre una familia affine debe aportar un binding explícito
   `quantity_kind: ABSOLUTE | INTERVAL` para cada símbolo implicado;
3. el binding forma parte del contexto y de su hash derivado;
4. si falta o la salida derivada contradice el binding esperado, se emite
   `AFFINE_QUANTITY_ERROR` y no se evalúa;
5. ninguna operación presume que dos valores en °C son sumables como absolutos.

El Implementation Plan deberá decidir si esta estrategia contextual basta para v1 o si propone
una extensión gobernada mediante un sucesor de modelo. No podrá editar contratos históricos en
silencio.

**ARCHITECTURAL_COMPATIBILITY_FINDING GDSS2-CF-02:** `GdssOperation` no contiene una operación
de evaluación. Esto no bloquea la arquitectura, pero el plan debe definir y probar el mapeo sin
inferir que lectura, publicación o rol global conceden evaluación automáticamente.

**ARCHITECTURAL_COMPATIBILITY_FINDING GDSS2-CF-03:** `canonical_unit` es texto dentro de la
revisión de unidad, no una FK versionada a otra definición, y GDSS-001 no valida una familia de
conversión completa. El plan debe decidir cómo construir y validar un catálogo cerrado por modelo
antes de convertir. Una unidad canónica ausente, ambigua o incoherente falla con
`INVALID_INPUT_UNIT`; no se consulta un catálogo global implícito.

## 9. Dependencias y ciclos

Cada referencia única del AST crea una arista directa desde la fórmula hacia el símbolo. Si el
símbolo de salida es producido por otra fórmula del mismo modelo, puede derivarse transitividad.
Referencias duplicadas colapsan como conjunto, coherente con P3 de GDSS-001. Construcción y
orden serializado son deterministas.

El grafo es computacional, no causal ni temporal. Un algoritmo determinista de componentes
fuertemente conexas detectará ciclos, incluidos self-loops. Un ciclo produce
`CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS`, impide evaluación algebraica DAG y no declara
falsedad científica. GDSS-002 no incorpora solver.

## 10. Evaluación y lifecycle

Un `EvaluationContext` incluye el identificador exacto de versión y fórmula, versiones de
lenguaje/evaluador, valores, unidades y bindings affine explícitos. No existe lookup implícito.
Un modelo válido puede carecer de inputs y no ser evaluable ahora.

La evaluación de `DRAFT` puede habilitarse como operación explícita de autoría; versiones
congeladas permiten reproducción. En todos los estados el resultado es `DERIVED`, efímero y sin
promoción epistemológica. Éxito o fallo no modifica contenido, lifecycle, procedencia o auditoría
de publicación.

## 11. Autorización

Se reutiliza identidad OAuth, scope y roles por proyecto de GDSS-001. No se crea identidad
paralela. Arquitectura exige una operación distinguible `EVALUATE_MODEL`; el Implementation Plan
resolverá si se mapea a `read`, `operator` o un permiso nuevo a partir de evidencia del repositorio.

```text
EVALUATE ≠ VALIDATE ≠ APPROVE ≠ PUBLISH ≠ ACTUATE
```

Ningún resultado puede autorizar algo físico, directa o indirectamente. Publicación tampoco
confiere esa autoridad.

## 12. Límites obligatorios

Antes de evaluar deben existir límites positivos y comprobados para longitud de fuente, tokens,
profundidad y nodos AST, referencias, anidamiento de funciones, nodos y aristas del grafo y
cantidad de inputs. La arquitectura fija como techos externos los ya gobernados por GDSS-001:
fuente ≤ 2000 caracteres, identificador ≤ 120 y contenido ≤ 1000 hijos/refs por fórmula. El plan
seleccionará límites internos más estrictos con benchmarks. Superarlos siempre produce
`RESOURCE_LIMIT_EXCEEDED`; no hay evaluación parcial.

## 13. Diagnósticos y etapas

```text
SOURCE → PARSED → SYMBOL_RESOLVED → DIMENSIONALLY_VALIDATED → EVALUABLE
```

Cada etapa se alcanza sólo si la anterior terminó sin error. Los diagnósticos llevan código,
etapa, severidad, fórmula, span, símbolo, expected, actual y mensaje. El código es identidad
canónica; el mensaje no.

## 14. Neutralidad y fronteras

Casos hidropónico y térmico deberán usar el mismo parser, AST, resolver, álgebra y evaluador. El
núcleo no contendrá vocabulario de dominio. No dependerá de Control Engine, DTE, MQTT ni
actuación, ni reutilizará sus internals.

GDSS-002 entiende matemática gobernada. No observa, simula, predice, recomienda, controla ni
actúa. La regla permanente es:

> **Executable mathematics does not confer executable physical authority.**

## 15. Consecuencias para el futuro plan

El Implementation Plan deberá elegir estrategia de parser sin runtime general, representación
canónica binary64, límites medidos, algoritmo y orden del grafo, API pura, mapeo RBAC, hashes
derivados, pruebas de neutralidad y abuso, y resolución explícita de `GDSS2-CF-01`. No hay
autorización para implementar estas decisiones.
