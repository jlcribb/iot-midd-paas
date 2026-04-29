# parametric-control-engine

Motor MVP de control parametrico monovariable para Midd IOT.

Su alcance inicial es deliberadamente acotado:

- recibir la definicion de una variable controlada;
- recibir una medicion o estado actual;
- recibir una referencia objetivo;
- calcular error;
- aplicar una funcion de control parametrica simple;
- devolver una recomendacion de accion con traza completa.

Este componente no implementa todavia:

- MPC;
- control multivariable;
- actuacion directa sobre hardware;
- integracion profunda con superficies legacy.

## Estado

Estado actual: `mvp-initial`

## Estructura

```text
apps/parametric-control-engine/
  README.md
  src/parametric_control_engine/
    adapters/
    contracts/
    evaluators/
    examples/
    models/
    policies/
    sources/
    trace/
  tests/
```

## Modulos principales

- `contracts/`
  - contratos de entrada y salida del motor.
- `adapters/`
  - adaptadores entre eventos externos, evaluacion de control y sobres de salida.
- `models/`
  - definiciones de variable, estado, setpoint, parametros y resultado.
- `policies/`
  - seleccion estatica y trazable de bindings de control.
- `sources/`
  - origenes de politicas desacoplados del selector.
- `evaluators/`
  - implementaciones concretas de funciones de control.
- `trace/`
  - utilidades para construir trazas evaluables paso a paso.
- `examples/`
  - ejemplos ejecutables del MVP.

## Contrato de entrada

El MVP trabaja con un `ControlEvaluationRequest` compuesto por:

- `variable`
  - definicion de la variable controlada y del actuador sugerido;
- `measurement`
  - valor observado y metadatos basicos de la medicion;
- `setpoint`
  - referencia objetivo;
- `parameters`
  - ganancia, banda muerta y limites de la recomendacion;
- `context`
  - metadatos opcionales para trazabilidad operacional.

## Contrato de salida

El resultado es un `ControlEvaluationResponse` con:

- `error`
  - diferencia entre setpoint y medicion;
- `raw_control_signal`
  - salida directa de la funcion parametrica;
- `recommendation`
  - accion sugerida, magnitud y resumen humano;
- `trace`
  - pasos detallados de la evaluacion;
- `evaluator_name`
  - nombre de la estrategia aplicada;
- `evaluated_at`
  - marca temporal de la evaluacion.

## Evaluador inicial

El primer evaluador implementado es `ProportionalEvaluator`.

Funcion:

```text
error = setpoint - measurement
raw_control_signal = gain * error
```

Luego aplica:

- banda muerta (`deadband`);
- magnitud minima (`min_action`);
- saturacion maxima (`max_action`);
- direccion de control (`controller_direction`).

## Comparacion experimental: threshold vs proportional

Para validar el MVP tambien se incluye una comparacion experimental simple entre:

- control por umbrales (`ThresholdEvaluator`);
- control parametrico proporcional (`ProportionalEvaluator`).

El objetivo no es realismo fisico, sino comparar comportamientos sobre la misma
secuencia sintetica de mediciones.

La comparacion reporta por paso:

- medicion;
- setpoint;
- accion elegida;
- senal aplicada;
- traza;

Y ademas resume por estrategia:

- cantidad de `hold`;
- cambios de accion;
- error absoluto acumulado;
- error cuadratico acumulado;
- esfuerzo total aplicado;
- distancia promedio al setpoint;
- magnitudes no nulas observadas.

Interpretacion esperada:

- `threshold` produce acciones mas bruscas y menos graduadas;
- `proportional` modula la magnitud segun el error;
- `threshold` suele cambiar menos de magnitud;
- `proportional` ofrece una respuesta mas fina cerca del setpoint.

Guia de lectura rapida:

- menor `cumulative_absolute_error` implica menor desvio acumulado;
- menor `cumulative_squared_error` penaliza menos los errores grandes;
- menor `total_applied_effort` implica una estrategia menos agresiva;
- menor `average_distance_to_setpoint` indica mejor cercania media al objetivo;
- `unique_nonzero_signals` ayuda a visualizar si la estrategia actua en escalones fijos o de forma graduada.

Comparacion abierta vs cerrada:

- la comparacion abierta usa una secuencia fija de mediciones y sirve para comparar la forma de las recomendaciones;
- la comparacion cerrada agrega una planta sintetica de primer orden y deja que las acciones modifiquen la evolucion del estado;
- en la comparacion cerrada las metricas de error pueden divergir entre estrategias, no solo las de esfuerzo.

## Closed-loop benchmark MVP

El benchmark cerrado agrega tres escenarios sinteticos estandar:

1. `large_initial_error`
2. `sustained_disturbance`
3. `near_setpoint_operation`

Cada escenario corre ambas estrategias sobre:

- misma condicion inicial;
- mismo setpoint;
- mismo horizonte;
- misma planta;
- misma secuencia de perturbaciones.

La salida incluye:

- tabla compacta de benchmark;
- resumen por escenario;
- trayectorias completas;
- interpretacion corta para lectura de MVP.

Lectura sugerida:

- `threshold` suele rendir mejor cuando se acepta accion mas brusca para corregir rapido;
- `proportional` suele rendir mejor cuando se prioriza menor esfuerzo y modulacion fina;
- conviene leer error y esfuerzo juntos, no aislar una sola metrica.

## Presentation-ready benchmark

Sobre el benchmark cerrado tambien hay una capa de formato lista para:

- slides;
- documentos Markdown;
- pitch materials;
- resúmenes ejecutivos.

Salidas disponibles:

- `scorecard`
  - vista compacta por escenario con ganadores por metrica;
- `markdown_table`
  - tabla lista para pegar en README, docs o slides;
- `executive_summary`
  - bloque breve con lectura de negocio/MVP.

## Persistent benchmark artifacts

El benchmark tambien puede exportarse como snapshot persistente en:

- `docs/benchmark/mvp_benchmark.md`
- `docs/benchmark/mvp_benchmark.json`

Comando de regeneracion:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.export_benchmark_artifacts
```

Ese comando:

- recalcula el benchmark actual;
- genera el reporte Markdown;
- genera el snapshot JSON;
- deja una base estable para comparacion futura.

## Adapter evento -> recomendacion

El siguiente corte del MVP agrega un adaptador minimo para conectar un evento de
telemetria o estado con el evaluador proporcional.

Contratos:

- `TelemetryStateEvent`
  - evento externo minimo con `event_id`, `variable_id`, `value`, `source` y contexto;
- `MonovariableControlBinding`
  - enlace estatico entre una variable, un setpoint, parametros y un canal de recomendacion;
- `EventDrivenRecommendation`
  - salida estructurada para futura integracion con workers, colas o runtime.

Uso esperado:

1. llega un evento de telemetria;
2. el adapter lo convierte en `ControlEvaluationRequest`;
3. el evaluador proporcional calcula error y recomendacion;
4. el adapter devuelve un sobre con:
   - resultado de evaluacion;
   - traza del adapter;
   - `runtime_payload` listo para integracion posterior.

## Adapter recomendacion -> publish/persist envelope

El siguiente corte del MVP agrega una capa final de salida agnostica:

- `PublishableRecommendationEnvelope`
  - sobre listo para futura publicacion en bus, cola o broker;
- `RecommendationAuditEnvelope`
  - sobre listo para futura persistencia o auditoria;
- `RecommendationSinkOutput`
  - resultado conjunto con traza del sink adapter.

Uso esperado:

1. ya existe un `EventDrivenRecommendation`;
2. el sink adapter construye:
   - un envelope publicable;
   - un envelope persistible;
   - una traza de salida;
3. otra capa futura decide si publica, persiste o ambas.

Flujo conceptual completo del MVP:

```text
telemetry event
  -> control evaluation request
  -> proportional recommendation
  -> publish envelope
  -> persist envelope
```

## Policy selection

El siguiente corte del MVP agrega una capa minima de seleccion de politica.

Contratos:

- `PolicySelectionRequest`
  - entrada minima para resolver una politica por `variable_id` y contexto;
- `StaticPolicyDefinition`
  - binding estatico con filtros de contexto opcionales;
- `PolicySelectionResult`
  - politica resuelta y traza de seleccion.

Implementacion inicial:

- `InMemoryPolicySource`
  - fuente desacoplada de politicas estaticas en memoria;
- `StaticPolicySelector`
  - consume un `policy source` y resuelve un `MonovariableControlBinding` usando:
    - `variable_id`;
    - filtros exactos de contexto;
    - preferencia por la politica mas especifica.

Abstraccion agregada:

- `PolicySourceRequest`
  - consulta minima hacia una fuente de politicas;
- `PolicySourceResult`
  - politicas candidatas y traza de carga.

Rol arquitectonico:

- hoy la fuente puede ser en memoria;
- hoy resuelve bindings estaticos;
- manana el origen puede venir de `cognitive-core` o configuracion de dominio;
- manana puede ser reemplazado o enriquecido por `cognitive-core`;
- el resto del pipeline no necesita cambiar.

Flujo conceptual ampliado:

```text
telemetry event
  -> policy source
  -> policy selection
  -> control evaluation request
  -> proportional recommendation
  -> publish envelope
  -> persist envelope
```

## Ejemplo ejecutable

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.tank_level_demo
```

Ese ejemplo simula una recomendacion para el nivel de un tanque usando una valvula de ingreso.

Ejemplo orientado a eventos:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.event_driven_demo
```

Ese ejemplo muestra la transformacion completa:

- evento de estado;
- request interno de control;
- recomendacion estructurada;
- trazas del adapter y del evaluador.

Ejemplo de pipeline completo:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.recommendation_pipeline_demo
```

Ese ejemplo muestra de punta a punta:

- evento de telemetria;
- recomendacion evaluada;
- sobre publicable;
- sobre persistible;
- trazas de cada etapa.

Ejemplo con seleccion de politica:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.policy_selected_pipeline_demo
```

Ese ejemplo muestra:

- evento de telemetria;
- resolucion de politica estatica;
- evaluacion de control;
- sobres de salida;
- trazas del selector, evaluador y sink.

Ejemplo con `policy source` desacoplado:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.policy_source_pipeline_demo
```

Ese ejemplo muestra:

- consulta a una fuente de politicas en memoria;
- seleccion de politica;
- evaluacion de control;
- sobres publicables y persistibles.

Ejemplo comparativo:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.threshold_vs_proportional_demo
```

Ese ejemplo muestra:

- mismo escenario monovariable;
- misma secuencia de mediciones;
- salida estructurada para `threshold` y `proportional`;
- metricas reproducibles de comparacion.

Ejemplo comparativo en lazo cerrado:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.closed_loop_threshold_vs_proportional_demo
```

Ese ejemplo agrega:

- planta sintetica de primer orden;
- misma condicion inicial para ambas estrategias;
- misma secuencia de perturbaciones;
- trayectorias de estado y metricas de error comparables.

Benchmark cerrado de escenarios:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.closed_loop_benchmark_demo
```

Ese ejemplo muestra:

- tres escenarios estandar;
- tabla compacta por estrategia;
- resumen interpretativo del benchmark.

Benchmark listo para presentacion:

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/python -m parametric_control_engine.examples.closed_loop_benchmark_scorecard_demo
```

Ese ejemplo imprime:

- scorecard compacto;
- tabla Markdown;
- resumen ejecutivo corto.

## Pruebas

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_proportional_evaluator.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_event_adapter.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_recommendation_sink_adapter.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_static_policy_selector.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_in_memory_policy_source.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_threshold_evaluator.py \
  apps/parametric-control-engine/tests/test_threshold_vs_proportional_comparison.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_first_order_simulation.py \
  apps/parametric-control-engine/tests/test_closed_loop_threshold_vs_proportional_comparison.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_closed_loop_benchmark_suite.py
```

```bash
PYTHONPATH=apps/parametric-control-engine/src \
./venv/bin/pytest apps/parametric-control-engine/tests/test_benchmark_formatter.py
```

## Conexion futura con el resto de la arquitectura

### Con `cognitive-core`

El `cognitive-core` podra:

- proveer politicas candidatas a traves de una fuente futura;
- seleccionar la estrategia de control adecuada;
- reemplazar o enriquecer la seleccion estatica de politicas;
- ajustar parametros en tiempo de ejecucion;
- enriquecer el `context` con reglas, riesgo o estado operativo;
- decidir si una recomendacion debe ejecutarse, degradarse o bloquearse.

### Con el runtime IoT Python

El runtime Python podra:

- tomar una medicion desde ingesta o storage;
- adaptar un evento MQTT/telemetrico a `TelemetryStateEvent`;
- consultar una `policy source` desacoplada;
- pedir al selector una politica/binding valido para ese evento;
- materializar un `ControlEvaluationRequest`;
- ejecutar el evaluador del motor;
- materializar envelopes publicables y persistibles sin acoplarse todavia a broker o base real;
- derivar la accion a una capa de control posterior sin acoplar el MVP al hardware.

Con el adapter nuevo, ese encaje ya queda mas directo:

- `ingestor` o un worker posterior puede entregar un evento simple;
- una fuente de politicas desacoplada entrega candidatos;
- el selector resuelve una politica estatica demostrable;
- el motor responde con un `runtime_payload` estructurado;
- el sink adapter prepara envelopes de salida;
- otra capa futura decide si persistir, publicar o eventualmente actuar.

## Criterio de evaluacion del MVP

El MVP queda listo para demo si puede mostrar claramente:

- entrada controlada;
- error calculado;
- senal de control generada;
- accion recomendada;
- traza interpretable paso a paso.
