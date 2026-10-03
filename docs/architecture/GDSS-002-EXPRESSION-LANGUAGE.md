# MIDD-IOT — GDSS-002
## GDSS_EXPR_V1 Specification v0.1

**Status:** `PROPOSED_FOR_REVIEW`
**Phase:** `GDSS-002`
**Canonical name:** Governed Safe Expression & Deterministic Evaluation Foundation
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Implementation:** `NOT_YET_AUTHORIZED`

## 1. Entrada y codificación

El parser recibe exactamente `Formula.expression_source` como texto Unicode. No acepta
asignación: la salida está en `Formula.output_ref`. La implementación futura normalizará y
comparará identificadores sólo por igualdad exacta de code points; no hará case folding,
normalización Unicode, corrección ortográfica ni aliasing. V1 admite únicamente tokens ASCII,
salvo whitespace Unicode reconocido de forma explícita por el tokenizer.

El límite externo actual es 2000 caracteres. Fuente vacía, NUL, caracteres de control no
whitespace o token fuera de la gramática fallan.

## 2. Léxico

```ebnf
DIGIT          = "0"…"9" ;
NONZERO        = "1"…"9" ;
LETTER         = "A"…"Z" | "a"…"z" ;
IDENTIFIER     = LETTER, { LETTER | DIGIT | "_" } ;
INTEGER_PART   = "0" | NONZERO, { DIGIT } ;
FRACTION_PART  = ".", DIGIT, { DIGIT } ;
EXPONENT_PART  = ("e" | "E"), [ "+" | "-" ], DIGIT, { DIGIT } ;
NUMBER         = INTEGER_PART, [ FRACTION_PART ], [ EXPONENT_PART ] ;
```

`IDENTIFIER` coincide con la clave local GDSS-001 y tiene máximo 120 caracteres. Tokens se
separan por operadores, paréntesis, coma o whitespace; no existe multiplicación implícita.

Válidos: `12`, `12.5`, `0.25`, `1e-3`, `2E6`. Inválidos: `.5`, `1.`, `01`, `1e`, `1e+`, hex,
binario, separadores `_`, `NaN`, `Infinity`, signos dentro del token y sufijos de unidad. El signo
es operador unario, no parte del literal.

Whitespace sólo separa tokens y no tiene significado. No existen comentarios.

## 3. Gramática

```ebnf
expression       = additive ;
additive         = multiplicative, { ("+" | "-"), multiplicative } ;
multiplicative   = unary, { ("*" | "/"), unary } ;
unary            = ("+" | "-"), unary | power ;
power            = primary, [ "^", unary ] ;
primary          = NUMBER
                 | IDENTIFIER
                 | function_call
                 | "(", expression, ")" ;
function_call    = FUNCTION_NAME, "(", argument_list, ")" ;
argument_list    = expression, { ",", expression } ;
FUNCTION_NAME    = "abs" | "min" | "max" | "sqrt"
                 | "exp" | "ln" | "log10" | "pow" ;
```

La alternativa `function_call` tiene prioridad cuando un identificador allowlisted está seguido
por `(`. Cualquier otro nombre seguido por `(` produce `UNSUPPORTED_FUNCTION`, no una referencia.

## 4. Precedencia y asociatividad

De mayor a menor:

1. literales, referencias, llamadas y paréntesis;
2. `^`, asociativo a derecha;
3. unarios `+` y `-`;
4. `*` y `/`, asociativos a izquierda;
5. `+` y `-` binarios, asociativos a izquierda.

Por tanto:

```text
-2^2   = -(2^2) = -4
2^3^2  = 2^(3^2) = 512
2^-2   = 2^(-2)
a/b*c  = (a/b)*c
```

Los paréntesis reemplazan precedencia. Cada par debe cerrar y la profundidad queda acotada por
el perfil de recursos.

## 5. Semántica de operadores

Todos los operandos y resultados son binary64 finitos y deben superar validación dimensional.

| Operador | Aridad | Numérico | Dimensional |
|---|---:|---|---|
| unario `+` | 1 | identidad | conserva dimensión y clase affine |
| unario `-` | 1 | negación finita | conserva dimensión; absoluto affine se rechaza por ambigüedad física |
| `+`, `-` | 2 | suma/resta | dimensiones iguales, conversión explícita y reglas affine |
| `*` | 2 | producto | suma vectores; absolutos affine prohibidos |
| `/` | 2 | cociente, divisor no cero | resta vectores; absolutos affine prohibidos |
| `^` | 2 | potencia real válida | reglas conservadoras de potencia |

No hay concatenación, coerción booleana ni overload por tipo de runtime.

## 6. Funciones permitidas

| Función | Aridad | Dominio numérico | Regla dimensional | Fallo |
|---|---:|---|---|---|
| `abs(x)` | 1 | finito | conserva dimensión; absoluto affine no permitido | domain/affine |
| `min(a,b,...)` | 2..16 | finitos | mismas dimensiones; conversión común; clases affine compatibles | mismatch/affine |
| `max(a,b,...)` | 2..16 | finitos | igual a `min` | mismatch/affine |
| `sqrt(x)` | 1 | `x >= 0` | cada exponente debe ser par; resultado divide exponentes por 2 | domain/dimension |
| `exp(x)` | 1 | resultado finito | argumento adimensional; resultado adimensional | domain/non-finite |
| `ln(x)` | 1 | `x > 0` | argumento y resultado adimensional | domain |
| `log10(x)` | 1 | `x > 0` | argumento y resultado adimensional | domain |
| `pow(b,e)` | 2 | como `b ^ e` | exactamente la semántica de `^` | domain/dimension |

Una base dimensionada sólo admite exponente entero expresado como literal constante, incluyendo
su forma unaria, y el vector resultante debe permanecer entero y dentro de los límites del plan.
Una base adimensional admite exponente adimensional no constante; una base negativa exige
exponente entero en runtime. Cero elevado a valor no positivo falla. No se producen complejos.

V1 no admite funciones trigonométricas: sus convenciones angulares requieren una decisión
posterior. La allowlist es cerrada; no existe dispatch dinámico.

## 7. Referencias y resolución

Un `IDENTIFIER` que no es llamada representa exactamente un `Child.symbol`. Debe:

1. existir una sola vez en el `SystemModelVersion` exacto;
2. ser `Variable` o `Parameter`;
3. figurar en `Formula.input_refs`;
4. no ser `Formula.output_ref` salvo que el futuro análisis de ciclos lo trate como self-loop.

El conjunto de referencias del AST debe ser idéntico a `input_refs` tras deduplicación. Referencia
extra o declarada pero ausente produce `DECLARED_DEPENDENCY_MISMATCH`. No hay globales,
propiedades, namespaces ni acceso cruzado de versión.

## 8. AST determinista

El parser genera exclusivamente `NumericLiteral`, `SymbolReference`, `UnaryExpression`,
`BinaryExpression` y `FunctionCall`. Preserva estructura, orden de operandos y span. No realiza
constant folding, conmutación ni simplificación durante parseo. Para la misma fuente y
`GDSS_EXPR_V1`, su serialización canónica es idéntica.

## 9. Exclusiones

Están prohibidos asignación, `=`, comparación, booleanos, statements, `;`, loops, condicionales,
arrays, objetos, strings, templates, lambdas, funciones de usuario, nombres dinámicos, acceso
`.`/`[]`, métodos, callbacks, comentarios, implicit multiplication, postfix operators, unidades
embebidas, imports y todo token no declarado.

Ejemplos que fallan:

```text
Q = A * v
2m
object.property
f[x]
constructor("return 1")
sqrt.call(x)
x > 0 ? x : 0
```

La forma válida del primer caso es `A * v` con `output_ref = Q`.

## 10. Fallos y límites

Errores léxicos o sintácticos no producen AST parcial evaluable. Operador conocido por el
tokenizer pero no permitido emite `UNSUPPORTED_OPERATOR`; token ajeno,
`UNSUPPORTED_TOKEN`; estructura inválida, `PARSE_ERROR`; función fuera de allowlist,
`UNSUPPORTED_FUNCTION`.

Se comprueban límites antes y durante tokenización/parseo. La implementación futura debe definir
y probar máximos positivos de tokens, nodos, profundidad y nesting por debajo de los techos del
ADR. El parser abandona de forma segura con `RESOURCE_LIMIT_EXCEEDED`.

## 11. Versionado

Cambiar gramática, precedencia, allowlist, aridad, dominio o significado requiere una nueva
versión de lenguaje. Corregir sólo la implementación sin cambiar semántica requiere nueva
`EvaluatorVersion` cuando pueda alterar resultados o diagnósticos reproducibles.
