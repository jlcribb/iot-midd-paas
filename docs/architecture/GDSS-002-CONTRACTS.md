# MIDD-IOT — GDSS-002
## Conceptual Contracts v0.1

**Status:** `PROPOSED_FOR_REVIEW`
**Phase:** `GDSS-002`
**Canonical name:** Governed Safe Expression & Deterministic Evaluation Foundation
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Implementation:** `NOT_YET_AUTHORIZED`

Estos contratos son conceptuales. No autorizan tipos, APIs, tablas ni migraciones.

## 1. Clasificación común

| Contrato | Clase | Propietario | Mutabilidad | Significado epistemológico |
|---|---|---|---|---|
| `ExpressionLanguageVersion` | VERSIONED DEFINITION | GDSS-002 | inmutable | convención computacional, no evidencia científica |
| `EvaluatorVersion` | VERSIONED DEFINITION | GDSS-002 | inmutable | implementación semántica identificada |
| `ParsedExpression`, `ExpressionAST`, `ASTNode` | DERIVED | fórmula + versión de lenguaje | regenerable | interpretación sintáctica |
| `SymbolReference`, `ResolvedSymbol` | DERIVED | fórmula + modelo exacto | regenerable | vinculación computacional local |
| `DependencyGraph` | DERIVED | modelo exacto | regenerable | dependencia, no causalidad |
| `DimensionalSignature`, `DimensionalAnalysis` | DERIVED | AST resuelto | regenerable | coherencia de unidades/dimensiones |
| `ExpressionValidation` | DERIVED | pipeline versionado | regenerable | validez computacional, no científica |
| `EvaluationContext`, `EvaluationInput` | EPHEMERAL | solicitud autorizada | inmutable durante operación | valores suministrados, no observaciones implícitas |
| `ExpressionEvaluationResult` | EPHEMERAL / DERIVED | operación de evaluación | inmutable | resultado computacional `DERIVED` |
| `EvaluationDiagnostic` | DERIVED | etapa que lo produce | inmutable | explicación computacional |

Ninguno tiene lifecycle propio. Todos refieren al `SystemModelVersion` y `Formula` gobernantes.

## 2. Versiones

### ExpressionLanguageVersion

```text
id: "GDSS_EXPR_V1"
grammar_revision
operator_semantics_revision
function_allowlist_revision
ast_schema_revision
```

Identifica gramática y significado, no un paquete incidental. Cambios incompatibles crean otro
identificador; nunca se muta una definición publicada.

### EvaluatorVersion

```text
id
expression_language_version
numeric_model: "IEEE754_BINARY64"
implementation_revision
derived_hash_schema_version
```

Permite atribuir orden de operaciones, serialización numérica y comprobaciones. No concede
autoridad operacional.

## 3. Parseo y AST

### ParsedExpression

```text
model_version_id
formula_symbol
source_expression
expression_language_version
ast
diagnostics
expression_ast_hash?  // separado de content_hash
```

Es regenerable y conserva el texto exacto. Un AST no reemplaza la fuente.

### ExpressionAST / ASTNode

Un árbol con raíz única y nodos cerrados:

```text
NumericLiteral { canonical_lexeme, finite_value, span }
SymbolReference { identifier, span }
UnaryExpression { operator: + | -, operand, span }
BinaryExpression { operator: + | - | * | / | ^, left, right, span }
FunctionCall { function_name, arguments[], span }
```

Los hijos tienen orden semántico. Cada span usa offsets Unicode code-point de inicio inclusivo y
fin exclusivo en `source_expression`; el plan deberá verificar el tratamiento de UTF-16 del
runtime elegido. La serialización AST es determinista y versionada, sin IDs aleatorios ni tiempo.

## 4. Símbolos

### SymbolReference

Referencia léxica por `Child.symbol`. No contiene label ni UUID adivinado.

### ResolvedSymbol

```text
model_version_id
local_symbol
artifact_kind: Variable | Parameter
unit_ref
dimension: [L,M,T,Theta,N,I,J]
quantity_kind?: ABSOLUTE | INTERVAL
source_span
```

Debe vincular exactamente una cantidad del mismo modelo. Cero o múltiples candidatos fallan;
Component, Formula, Constraint y Boundary son `INVALID_SYMBOL_KIND`. `quantity_kind` es binding
contextual obligatorio cuando interviene una familia affine, debido a `GDSS2-CF-01`.

## 5. Dependencias

### DependencyGraph

```text
model_version_id
nodes: ordered canonical set
direct_edges: ordered canonical set
transitive_edges: optional derived set
strongly_connected_components
topological_order?: only when acyclic
diagnostics
```

Una arista representa referencia matemática. Duplicados colapsan. El grafo no afirma causa,
tiempo o flujo físico. Un ciclo carece de orden topológico y requiere semántica dinámica futura.

## 6. Dimensiones

### DimensionalSignature

```text
known: true
exponents: [integer, integer, integer, integer, integer, integer, integer]
```

La ausencia de `known: true` no es dimensión adimensional. El vector cero sí lo es.

### DimensionalAnalysis

```text
model_version_id
formula_symbol
expression_language_version
node_results: [{ node_path, dimension, unit_semantics, quantity_kind? }]
output_dimension
output_quantity_kind?
conversions
status
diagnostics
```

Es regenerable. `conversions` explica unidad origen, canónica/destino, scale, offset, clase affine
y fórmula aplicada.

## 7. Validación

### ExpressionValidation

```text
model_version_id
formula_symbol
stage: SOURCE | PARSED | SYMBOL_RESOLVED | DIMENSIONALLY_VALIDATED | EVALUABLE
status: VALID | INVALID | VALID_BUT_MISSING_INPUTS | REQUIRES_DYNAMIC_SEMANTICS
language_version
evaluator_version?
diagnostics[]
```

El estado nunca eleva lifecycle ni procedencia. `VALID_BUT_MISSING_INPUTS` no es modelo inválido.

## 8. Evaluación

### EvaluationInput

```text
symbol
value: finite binary64
unit_ref: { key, revision }
quantity_kind?: ABSOLUTE | INTERVAL
```

La clave y revisión de unidad son explícitas. No hay coerción desde strings, booleanos o valores
no finitos. Un input no autorizado por `input_refs` falla cerrado.

### EvaluationContext

```text
project_id
model_version_id
formula_symbol
expression_language_version
evaluator_version
inputs: exact symbol map
requested_output_unit?: { key, revision }
expected_output_quantity_kind?: ABSOLUTE | INTERVAL
resource_limits_profile
```

Es inmutable durante la operación, scoped al proyecto y libre de clientes externos. Su hash
derivado incluye unidades, quantity kinds, versiones y límites relevantes.

### ExpressionEvaluationResult

```text
model_version_id
formula_symbol
expression_language_version
evaluator_version
status: SUCCEEDED | FAILED
normalized_inputs
result?: { finite_value, unit_ref, dimension, quantity_kind? }
dimensional_derivation
diagnostics[]
expression_ast_hash
evaluation_input_hash
evaluation_result_hash?
epistemic_kind: DERIVED
physical_authority: NONE
```

Es efímero en GDSS-002. Un fallo no ofrece resultado parcial. Éxito no significa observado,
predicho, calibrado, validado científicamente ni publicado.

## 9. Diagnósticos

### EvaluationDiagnostic

```text
code
stage
severity: ERROR | WARNING | INFO
model_version_id
formula_symbol
span?: { start, end }
symbol?: string
expected?: structured value
actual?: structured value
message
```

Códigos mínimos:

```text
PARSE_ERROR
UNSUPPORTED_TOKEN
UNSUPPORTED_OPERATOR
UNSUPPORTED_FUNCTION
UNKNOWN_SYMBOL
AMBIGUOUS_SYMBOL
CROSS_VERSION_REFERENCE
INVALID_SYMBOL_KIND
DECLARED_DEPENDENCY_MISMATCH
DIMENSION_MISMATCH
UNKNOWN_OR_MISSING_DIMENSION
AFFINE_QUANTITY_ERROR
INVALID_FUNCTION_DOMAIN
CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS
MISSING_INPUT
UNDECLARED_INPUT
INVALID_INPUT_UNIT
DIVISION_BY_ZERO
NON_FINITE_INPUT
NON_FINITE_RESULT
RESOURCE_LIMIT_EXCEEDED
```

`code`, no `message`, define identidad estable. Varios errores pueden acumularse sólo cuando no
requieren continuar con una representación insegura; nunca se evalúa tras un error.

## 10. Ownership, autorización y mutabilidad

Todos los derivados incluyen la versión exacta y la fórmula. No se mueven entre versiones aunque
el texto coincida. Evaluar exige scope del proyecto y una futura decisión de permiso
`EVALUATE_MODEL`; no implica editar, validar, aprobar o publicar. La operación no muta ninguna
tabla, aggregate, lifecycle o auditoría de GDSS-001.

## 11. Hashes derivados

Los hashes opcionales deben identificar esquema, versiones y representación canónica. No se
incluyen en `SystemModelVersion.content_hash` ni lo actualizan. `evaluation_result_hash` sólo
identifica bytes computacionales reproducibles; no certifica verdad científica.

## 12. Compatibilidad GDSS-001

- `expression_source`, `input_refs` y `output_ref` cubren fuente, dependencia declarada y salida.
- `symbol` es local, estable dentro de la versión y separado de `label`.
- dimensión y unidad son obligatorias para Variable/Parameter.
- la falta de `ABSOLUTE | INTERVAL` es el hallazgo `GDSS2-CF-01`; el binding contextual falla
  cerrado y no altera contratos existentes.
- la falta de una operación RBAC `EVALUATE_MODEL` es `GDSS2-CF-02`; su mapeo queda para el plan.
- `canonical_unit` no es una referencia versionada ni garantiza una familia completa
  (`GDSS2-CF-03`); toda conversión futura validará un catálogo cerrado y fallará si es ambiguo.
# Post-closure extension notice

`GDSS_UNIT_CONVERSION_V1` remains immutable. `GDSS_UNIT_CONVERSION_V2` is an explicitly selected
successor that preserves V1 and adds canonical interval unit `second@1`. This notice does not
retroactively change the original contracts; the normative delta is recorded in
`GDSS-002-TEMPORAL-UNIT-EXTENSION.md`.
