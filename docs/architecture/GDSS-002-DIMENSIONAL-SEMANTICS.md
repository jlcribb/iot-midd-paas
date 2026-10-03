# MIDD-IOT — GDSS-002
## Dimensional Semantics v0.1

**Status:** `PROPOSED_FOR_REVIEW`
**Phase:** `GDSS-002`
**Canonical name:** Governed Safe Expression & Deterministic Evaluation Foundation
**Baseline:** `295b521bb19eb77cba663d8df4b241a56f909e0c`
**Implementation:** `NOT_YET_AUTHORIZED`

## 1. Modelo dimensional

GDSS-002 conserva la firma entera de GDSS-001:

```text
D = [L, M, T, Θ, N, I, J] ∈ Z⁷
```

El orden es normativo. Igualdad exige siete exponentes enteros iguales. El vector cero es una
dimensión conocida `DIMENSIONLESS`. Campo ausente, longitud distinta, exponente no entero o
estado desconocido produce `UNKNOWN_OR_MISSING_DIMENSION`; nunca se convierte al vector cero.

## 2. Unidad y normalización

Una revisión de unidad GDSS-001 aporta `dimension`, `scale`, `offset` y `canonical_unit`.
Conceptualmente, para cantidad absoluta:

```text
canonical_value = value * scale + offset
value = (canonical_value - offset) / scale
```

Para intervalo:

```text
canonical_delta = delta * scale
delta = canonical_delta / scale
```

La clave y revisión exactas son parte del input. Misma dimensión no autoriza usar valores sin
conversión. Scale debe ser positivo y todo cálculo debe permanecer finito. Dado `GDSS2-CF-03`,
`canonical_unit` no se acepta por sí solo como prueba de una cadena de conversión: el catálogo
derivado del modelo debe contener una única definición coherente o la conversión falla.

## 3. Álgebra por operador

### Adición y sustracción

Requieren dimensiones iguales. Ambos operandos se normalizan a una unidad canónica común antes
de operar; la salida se convierte explícitamente a su unidad gobernada.

Para unidades lineales/intervalos:

```text
D + D → D
D - D → D
```

Para cantidades affine se aplican las reglas de la sección 6.

### Multiplicación

```text
[a₁…a₇] * [b₁…b₇] → [a₁+b₁ … a₇+b₇]
```

Los exponentes resultantes deben ser enteros representables y acotados. Una cantidad absoluta
affine debe convertirse o combinarse según semántica explícita antes; multiplicarla como valor
con offset es inválido.

### División

```text
[a₁…a₇] / [b₁…b₇] → [a₁-b₁ … a₇-b₇]
```

Además de las reglas de multiplicación, divisor cero falla antes de producir resultado.

### Potencia

Para base dimensionada, el exponente debe ser literal entero adimensional `n`:

```text
[a₁…a₇] ^ n → [n·a₁ … n·a₇]
```

No se redondean exponentes. Exponentes fraccionarios para bases dimensionadas quedan fuera de v1,
salvo `sqrt` bajo su regla exacta. Base adimensional con exponente adimensional permanece
adimensional y debe satisfacer dominio real.

## 4. Funciones

| Función | Requisito de entrada | Resultado dimensional |
|---|---|---|
| `abs(x)` | dimensión conocida; no absoluto affine ambiguo | `D(x)` |
| `min/max` | todas las dimensiones iguales y unidades convertibles | dimensión común |
| `sqrt(x)` | cada exponente de `D(x)` es par | `D(x)/2` componente a componente |
| `exp(x)` | `D(x) = 0` | dimensión cero |
| `ln(x)` | `D(x) = 0`, valor > 0 | dimensión cero |
| `log10(x)` | `D(x) = 0`, valor > 0 | dimensión cero |
| `pow(b,e)` | reglas de potencia y `D(e) = 0` | según base/exponente |

La coherencia dimensional no sustituye el dominio numérico ni la finitud.

## 5. Dimensión de salida

La dimensión derivada de la raíz AST debe ser exactamente igual a la dimensión de la cantidad
resuelta por `Formula.output_ref`. La unidad destino debe pertenecer a esa dimensión. Una
diferencia emite `DIMENSION_MISMATCH`; no se reescribe el modelo ni se infiere otra salida.

## 6. Cantidades affine: absoluto frente a intervalo

GDSS-001 no codifica esta clase semántica. `offset != 0` identifica una conversión affine, pero
no demuestra si un símbolo representa temperatura absoluta o diferencia. Por eso cada símbolo
involucrado requiere binding explícito `ABSOLUTE` o `INTERVAL`; ausencia produce
`AFFINE_QUANTITY_ERROR`.

Reglas v1:

| Operación | Resultado |
|---|---|
| `ABSOLUTE - ABSOLUTE` | `INTERVAL` |
| `ABSOLUTE + INTERVAL` | `ABSOLUTE` |
| `INTERVAL + ABSOLUTE` | `ABSOLUTE` |
| `ABSOLUTE - INTERVAL` | `ABSOLUTE` |
| `INTERVAL + INTERVAL` | `INTERVAL` |
| `INTERVAL - INTERVAL` | `INTERVAL` |
| `ABSOLUTE + ABSOLUTE` | error |
| `INTERVAL - ABSOLUTE` | error |
| multiplicar/dividir/potenciar absoluto affine | error |

Un intervalo puede participar en multiplicación/división usando sólo scale. Negar, `abs`,
`min/max` sobre absolutos affine queda rechazado en v1 salvo que una semántica inequívoca se
apruebe posteriormente. Comparación no existe en el lenguaje v1.

Ejemplos:

```text
20 °C absoluto → 293.15 K absoluto
Δ10 °C intervalo → Δ10 K intervalo
20 °C absoluto - 10 °C absoluto → Δ10 °C
20 °C absoluto + Δ10 °C → 30 °C absoluto
20 °C absoluto + 10 °C absoluto → AFFINE_QUANTITY_ERROR
```

La clase derivada debe coincidir con `expected_output_quantity_kind` cuando la salida sea affine.
Este binding contextual se incluye en hashes reproducibles y no altera GDSS-001.

## 7. Conversiones en suma, min y max

El validador elige como espacio de cálculo la unidad canónica de la dimensión, normaliza cada
operando con su revisión exacta y sólo entonces opera. `min/max` exige además clases affine
compatibles; en v1 se permite para intervalos y unidades lineales, no para absolutos affine.

Las conversiones se registran en `DimensionalAnalysis` con origen, destino, fórmula, scale,
offset y clase. No hay selección automática basada sólo en símbolos textuales como `m`, `K` o
`°C`.

## 8. Constantes literales

Un literal aislado es adimensional. V1 no tiene literales con unidad. Por ello sumar `2` a una
longitud es incompatible, mientras multiplicar una longitud por `2` es válido. Cero no obtiene
automáticamente la dimensión del otro operando en suma; no existe excepción de “cero universal”.

## 9. Validación y evaluación

El análisis dimensional ocurre sobre AST resuelto antes de evaluar. Si depende de un binding
affine ausente, no alcanza `DIMENSIONALLY_VALIDATED`. Inputs con unidad distinta pero compatible
se convierten explícitamente; unidad desconocida, revisión incorrecta o dimensión incompatible
produce `INVALID_INPUT_UNIT`.

No hay unknown-unit fallback, coerción silenciosa ni propagación de NaN. La explicación debe
mostrar la derivación de cada nodo y la conversión de cada input.

## 10. Compatibilidad y evolución

La firma entera de GDSS-001 limita potencias fraccionarias dimensionadas y se respeta. Extender a
exponentes racionales o persistir `ABSOLUTE | INTERVAL` exige una fase gobernada posterior. No se
redondearán exponentes ni se editará el `content_hash` histórico para sortear esa limitación.
