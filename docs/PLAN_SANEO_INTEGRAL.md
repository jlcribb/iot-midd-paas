# Plan De Saneo Integral

## Objetivo

Convertir el proyecto en una base operable y mantenible, con:

- arranque reproducible;
- modelo de datos coherente;
- API mínima funcional;
- autenticacion y autorizacion alineadas con el dominio;
- pruebas que protejan los flujos reales;
- documentacion veraz.

## Estado Actual (2026-03-25)

- Completado: SAN-020, SAN-021, SAN-030, SAN-031, SAN-033 (fase core tecnica).
- Completado: SAN-003 baseline automatizado con script reproducible.
- En curso: SAN-032 aislamiento de legado fuera del runtime principal.
- Pendiente: SAN-010 (ADR formal), SAN-022 (separacion local/produccion), documentacion principal consolidada.

### Hecho vs dicho (sincronizacion)

- Hecho:
- se elimino el paquete `demo` del runtime (`src/iot_middleware/demo/*`);
- se eliminaron modulos huérfanos (`api/rest.py`, `utils/auditoria_middleware.py`);
- se aislo el stack multiprotocolo legacy retirando exports y modulos (`services/unified_ingestor.py`, `input/connector_factory.py`, `input/input_manager.py`, `input/protocols/*`);
- `iot_middleware.input` quedo reducido a contrato base (`BaseConnector`, `UnifiedDataFormat`, `DataQuality`) para compatibilidad de tests actuales;
- baseline core ejecuta en verde con 17 tests.

- Alineado con el plan:
- SAN-011: delimitacion demo/legacy aplicada en runtime principal;
- SAN-032: avance material, pero aun queda retirar/aislar tablas SQL legacy (`sensor_data/devices/sensors`) del `db_handler`.

- No cerrado aun:
- SAN-010: falta ADR formal de arquitectura;
- SAN-022: falta perfilado explicito local/produccion;
- saneo de documentacion raiz (`README*.md`) para remover referencias a modulos retirados.

### Evidencia de cierre reciente

- `scripts/smoke_core.sh` como comando unico de smoke.
- `docs/SANEO_BASELINE.md` con comandos canonicos y warnings conocidos.
- Suite core actual: 17 tests pasando en bloque de saneamiento.

## Principios

- No agregar nuevas features hasta estabilizar el nucleo.
- Priorizar contratos compartidos sobre refactors cosmeticos.
- Cada fase debe cerrar con verificacion automatizable.
- Si una pieza "demo" y otra "productiva" compiten, se elige una sola.

## Diagnostico Base

### Problemas estructurales

- Existen dos arquitecturas de persistencia mezcladas: una simple (`sensor_data/devices/sensors`) y otra de dominio completo (`clientes/proyectos/unidades/dispositivos/canales/registros_datos`).
- La API, auth y los repositorios no comparten un contrato estable de nombres de campos.
- El modelo de permisos usa atributos inexistentes en `Usuario` y no el modelo real `UsuarioScope`.
- El arranque invoca constructores con firmas incompatibles.
- La cobertura de tests no protege los flujos de mayor riesgo.

### Definicion de exito

Se considerara saneado el nucleo cuando:

- `main.py` y la API arranquen sin parches manuales;
- exista un flujo funcional de healthcheck, autenticacion, escritura y lectura de datos;
- los tests core pasen en CI;
- la documentacion principal refleje el estado real;
- los secretos salgan de configuracion versionada.

## Alcance

### Incluido

- configuracion;
- bootstrap;
- persistencia;
- modelos;
- auth/scope;
- routers API;
- auditoria;
- pruebas;
- CI;
- documentacion principal.

### Excluido de esta primera ola

- rediseño visual del dashboard/admin;
- optimizaciones avanzadas de rendimiento;
- nuevas integraciones de protocolos no indispensables;
- nuevas funcionalidades de negocio.

## Estrategia

### Decision recomendada

Mantener como arquitectura principal el modelo ORM de dominio completo:

- `Cliente`
- `Proyecto`
- `UnidadProyecto`
- `Dispositivo`
- `Canal`
- `RegistroDatos`
- `EventoAlarma`
- `Usuario`
- `UsuarioScope`

Y retirar del runtime principal el camino alterno basado en:

- `sensor_data`
- `devices`
- `sensors`

Ese camino puede quedar, si hace falta, como modo demo o legado, pero no debe competir con el flujo principal.

## Backlog Ejecutivo

### Fase 0 - Contencion y linea base

#### SAN-001 Bloquear crecimiento del alcance

- Tipo: gobierno
- Prioridad: critica
- Objetivo: congelar nuevas features hasta estabilizar el nucleo.
- Tareas:
- etiquetar issues/incidencias como `saneo`, `feature`, `bloqueado`;
- declarar branch o milestone de saneo;
- marcar modulos experimentales.
- Criterios de aceptacion:
- existe una politica simple de trabajo para el saneo;
- el equipo sabe que solo se aceptan fixes del nucleo.

#### SAN-002 Inventario tecnico verificable

- Tipo: analisis
- Prioridad: critica
- Objetivo: establecer el mapa real del sistema.
- Tareas:
- listar entrypoints reales;
- listar dependencias runtime obligatorias;
- listar modulos legacy/duplicados;
- registrar estado actual de tests.
- Criterios de aceptacion:
- existe una tabla con modulos `activo`, `legacy`, `roto`, `experimental`.

#### SAN-003 Baseline automatizado

- Tipo: calidad
- Prioridad: critica
- Objetivo: fijar una linea base de ejecucion reproducible.
- Tareas:
- definir comando unico de smoke test;
- definir comando unico de test suite core;
- capturar warnings actuales conocidos.
- Criterios de aceptacion:
- cualquier desarrollador puede reproducir baseline local con 2-3 comandos.

### Fase 1 - Unificacion arquitectonica

#### SAN-010 ADR de persistencia y dominio

- Tipo: arquitectura
- Prioridad: critica
- Dependencias: SAN-002
- Objetivo: decidir y documentar la arquitectura oficial.
- Tareas:
- escribir una ADR corta;
- declarar si InfluxDB es primario, secundario o opcional;
- declarar si `sensor_data` queda eliminado o aislado como legado.
- Criterios de aceptacion:
- existe una unica ruta de persistencia principal;
- no quedan dudas sobre el modelo de datos oficial.

#### SAN-011 Delimitar modo demo/legacy

- Tipo: arquitectura
- Prioridad: alta
- Dependencias: SAN-010
- Objetivo: aislar codigo de demostracion del runtime principal.
- Tareas:
- identificar funciones de conveniencia y defaults peligrosos;
- mover o marcar helpers legacy;
- impedir que el runtime productivo use configuraciones hardcodeadas.
- Criterios de aceptacion:
- el arranque principal no depende de defaults embebidos.

### Fase 2 - Configuracion y bootstrap

#### SAN-020 Normalizar contrato de configuracion

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-010
- Objetivo: tener una configuracion consistente y validable.
- Tareas:
- unificar shape de config usado por `main.py`, `api.py`, MQTT y DB;
- decidir campos obligatorios y opcionales;
- eliminar placeholders ambiguos del flujo principal.
- Criterios de aceptacion:
- `load_config()` produce un objeto compatible con todos los consumidores core.

#### SAN-021 Corregir firmas de constructores y factories

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-020
- Objetivo: eliminar incompatibilidades de arranque.
- Tareas:
- alinear `create_database_handler()` con sus consumidores;
- alinear inicializacion de API, ingestor y monitoring;
- agregar validaciones tempranas de argumentos.
- Criterios de aceptacion:
- `main.py` y `initialize_api()` arrancan sin errores de firma.

#### SAN-022 Separar modo local y modo produccion

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-020
- Objetivo: evitar defaults inseguros o ambiguos.
- Tareas:
- introducir perfiles o archivos de config diferenciados;
- endurecer comportamiento por entorno;
- documentar variables de entorno requeridas.
- Criterios de aceptacion:
- existe una config minima local y otra de referencia para produccion.

### Fase 3 - Modelo de datos y persistencia

#### SAN-030 Unificar nomenclatura de campos

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-010
- Objetivo: eliminar la mezcla `metadata/metadatos`, `ultimo_login/ultimo_acceso`, etc.
- Tareas:
- definir naming canonical;
- corregir modelos, repositorios, routers y schemas;
- actualizar tests y docs.
- Criterios de aceptacion:
- no hay referencias cruzadas a nombres obsoletos en el codigo core.

#### SAN-031 Reparar `RegistroDatos` y su repositorio

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-030
- Objetivo: hacer funcional la escritura/lectura del dato central del sistema.
- Tareas:
- corregir mapping de metadatos;
- revisar clave primaria compuesta y warning ORM;
- asegurar que el repositorio devuelve objetos consistentes.
- Criterios de aceptacion:
- insertar y leer un dato de canal funciona mediante test de integracion.

#### SAN-032 Eliminar o aislar tablas manuales legacy

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-010
- Objetivo: evitar doble modelo de persistencia.
- Tareas:
- retirar `sensor_data/devices/sensors` del bootstrap principal;
- moverlas a modulo legacy o demo si se conservan;
- ajustar migraciones y documentacion.
- Criterios de aceptacion:
- el runtime principal no crea tablas fuera del modelo oficial.

#### SAN-033 Revisar migraciones y estrategia de schema

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-031
- Objetivo: que el schema lo controle Alembic y no `create_all()` indiscriminado.
- Tareas:
- definir si `create_all()` se usa solo en local/tests;
- revisar orden y consistencia de migraciones;
- validar particionamiento real de `registros_datos`.
- Criterios de aceptacion:
- existe una estrategia clara de bootstrap de esquema por entorno.

### Fase 4 - Auth, roles y scope

#### SAN-040 Rediseñar contrato de identidad

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-010
- Objetivo: alinear auth con el modelo real.
- Tareas:
- definir que contiene `Usuario`;
- definir que contiene `UsuarioScope`;
- decidir payload minimo del JWT.
- Criterios de aceptacion:
- el contrato de identidad no usa atributos inexistentes.

#### SAN-041 Reimplementar scope sobre `UsuarioScope`

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-040
- Objetivo: hacer que autorizacion y filtrado funcionen sobre datos reales.
- Tareas:
- reemplazar lecturas directas de `cliente_id/proyecto_id/unidad_id` en `Usuario`;
- resolver scopes activos desde relacion o consulta;
- encapsularlo en un servicio unico.
- Criterios de aceptacion:
- un usuario con scope limitado solo ve recursos permitidos en tests.

#### SAN-042 Endurecer middlewares y dependencias FastAPI

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-041
- Objetivo: evitar errores diferidos en runtime.
- Tareas:
- eliminar lambdas opacas como dependencia cuando correspondan;
- importar simbolos faltantes;
- unificar obtencion de usuario autenticado.
- Criterios de aceptacion:
- endpoints core fallan de forma controlada y tipada, no por `NameError` o `AttributeError`.

#### SAN-043 Corregir flujo de login/refresh/logout

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-040
- Objetivo: estabilizar el flujo de autenticacion.
- Tareas:
- corregir nombres de campos de ultimo acceso;
- definir manejo de refresh tokens;
- revisar hashing y expiracion;
- decidir si logout invalida realmente tokens.
- Criterios de aceptacion:
- login y refresh funcionan en tests de integracion.

### Fase 5 - API minima viable

#### SAN-050 Definir endpoints core

- Tipo: producto/backend
- Prioridad: critica
- Dependencias: SAN-021, SAN-031, SAN-041
- Objetivo: acotar la primera API estable.
- Alcance recomendado:
- `GET /health`
- `POST /auth/login`
- `GET /data/{canal_id}`
- `POST /datos/insertar`
- `GET /proyectos`
- Criterios de aceptacion:
- esos endpoints tienen contrato estable y pruebas.

#### SAN-051 Reparar routers y schemas

- Tipo: backend
- Prioridad: critica
- Dependencias: SAN-050
- Objetivo: alinear respuestas y DTOs.
- Tareas:
- corregir imports faltantes;
- eliminar referencias a atributos no existentes;
- unificar serializers.
- Criterios de aceptacion:
- los endpoints core responden con modelos validos.

#### SAN-052 Manejo de errores y codigos HTTP

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-051
- Objetivo: que la API falle bien.
- Tareas:
- introducir excepciones de dominio;
- mapear errores de repositorio y auth;
- revisar handlers globales.
- Criterios de aceptacion:
- los errores de negocio no salen como `500` generico si son previsibles.

### Fase 6 - Ingesta, monitoreo y auditoria

#### SAN-060 Estabilizar ingesta MQTT sobre el dominio oficial

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-031, SAN-041
- Objetivo: que la ingesta escriba en el modelo correcto.
- Tareas:
- revisar mapeo de topicos a proyecto/unidad/dispositivo/canal;
- revisar validacion por tipo/rango;
- revisar alarmas y metadatos enriquecidos.
- Criterios de aceptacion:
- un mensaje MQTT de prueba termina persistido y accesible por API.

#### SAN-061 Reencuadrar monitoreo como componente opcional

- Tipo: backend
- Prioridad: media
- Dependencias: SAN-021
- Objetivo: que monitoring no bloquee el arranque si RabbitMQ no esta operativo.
- Tareas:
- revisar inicializacion opcional;
- homogeneizar health/status de componentes;
- desacoplar del bootstrap principal.
- Criterios de aceptacion:
- el sistema puede operar sin monitoring si esta deshabilitado.

#### SAN-062 Reparar auditoria y sus tests

- Tipo: backend
- Prioridad: alta
- Dependencias: SAN-030
- Objetivo: estabilizar auditoria o degradarla explicitamente a opcional.
- Tareas:
- revisar servicio de auditoria;
- corregir contrato de tests obsoletos;
- decidir entidades realmente auditadas en MVP.
- Criterios de aceptacion:
- tests de auditoria reflejan el contrato real y pasan.

### Fase 7 - Seguridad

#### SAN-070 Externalizar secretos

- Tipo: seguridad
- Prioridad: critica
- Dependencias: SAN-020
- Objetivo: sacar credenciales y secretos del repo.
- Tareas:
- mover secretos a `.env` o secretos de contenedor;
- crear plantilla segura de ejemplo;
- rotar credenciales si alguna fue real.
- Criterios de aceptacion:
- no quedan secretos operativos versionados.

#### SAN-071 Endurecer CORS y auth por entorno

- Tipo: seguridad
- Prioridad: alta
- Dependencias: SAN-043
- Objetivo: evitar configuraciones inseguras por defecto.
- Tareas:
- parametrizar origins;
- evitar `*` con credenciales;
- activar auth en entornos no locales.
- Criterios de aceptacion:
- configuracion segura por defecto fuera de desarrollo local.

#### SAN-072 Revisar permisos y superficies expuestas

- Tipo: seguridad
- Prioridad: alta
- Dependencias: SAN-041
- Objetivo: garantizar minimo privilegio.
- Tareas:
- validar matriz rol-permiso;
- revisar endpoints publicos;
- revisar documentacion OpenAPI expuesta.
- Criterios de aceptacion:
- existe matriz rol-permiso documentada y verificada por tests.

### Fase 8 - Calidad, CI y pruebas

#### SAN-080 Redefinir piramide de pruebas

- Tipo: calidad
- Prioridad: critica
- Dependencias: SAN-050
- Objetivo: proteger los flujos reales del sistema.
- Tareas:
- separar unit, integration y smoke;
- eliminar o reescribir tests obsoletos;
- priorizar tests del nucleo sobre cobertura superficial.
- Criterios de aceptacion:
- existe una suite core pequena pero confiable.

#### SAN-081 Crear suite de integracion core

- Tipo: calidad
- Prioridad: critica
- Dependencias: SAN-031, SAN-043, SAN-051, SAN-060
- Objetivo: verificar extremo a extremo los casos principales.
- Casos minimos:
- arranque API;
- login;
- insercion de dato;
- consulta de dato por canal;
- filtros por scope;
- auditoria basica si aplica.
- Criterios de aceptacion:
- la suite corre en local y en CI.

#### SAN-082 Endurecer CI

- Tipo: calidad
- Prioridad: alta
- Dependencias: SAN-080
- Objetivo: convertir el saneo en una barrera automatica.
- Tareas:
- ejecutar lint, tests core y smoke;
- fallar por imports rotos y por tests criticos;
- reportar warnings deprecados como deuda controlada.
- Criterios de aceptacion:
- PRs al nucleo no entran sin validacion automatica.

### Fase 9 - Documentacion y operacion

#### SAN-090 Reescribir README principal

- Tipo: documentacion
- Prioridad: alta
- Dependencias: SAN-050
- Objetivo: reflejar solo capacidades verificadas.
- Tareas:
- simplificar promesas;
- documentar stack y arranque real;
- documentar modulos legacy si permanecen.
- Criterios de aceptacion:
- un desarrollador nuevo puede arrancar el sistema siguiendo el README.

#### SAN-091 Manual operativo minimo

- Tipo: documentacion
- Prioridad: media
- Dependencias: SAN-021, SAN-070, SAN-082
- Objetivo: dejar guias concretas para operar y depurar.
- Tareas:
- healthchecks;
- variables de entorno;
- migraciones;
- test suite;
- troubleshooting.
- Criterios de aceptacion:
- existe una guia corta de operacion local y despliegue basico.

## Secuencia Recomendada

### Sprint 1

- SAN-001
- SAN-002
- SAN-003
- SAN-010
- SAN-020
- SAN-021

### Sprint 2

- SAN-030
- SAN-031
- SAN-040
- SAN-041
- SAN-042

### Sprint 3

- SAN-043
- SAN-050
- SAN-051
- SAN-052
- SAN-080
- SAN-081

### Sprint 4

- SAN-032
- SAN-033
- SAN-060
- SAN-062
- SAN-070
- SAN-071
- SAN-082

### Sprint 5

- SAN-061
- SAN-072
- SAN-090
- SAN-091

## Camino Critico

El camino critico para lograr una base estable es:

1. SAN-010
2. SAN-020
3. SAN-021
4. SAN-030
5. SAN-031
6. SAN-040
7. SAN-041
8. SAN-043
9. SAN-050
10. SAN-051
11. SAN-081
12. SAN-082

Si ese camino se retrasa, el resto del saneo se vuelve maquillaje.

## Riesgos

### Riesgo 1: intentar arreglar ambas arquitecturas

- Impacto: alto
- Mitigacion: cerrar SAN-010 al inicio y hacer poda.

### Riesgo 2: corregir tests sin corregir contratos

- Impacto: alto
- Mitigacion: primero contratos, despues suite.

### Riesgo 3: introducir refactors masivos sin red de seguridad

- Impacto: alto
- Mitigacion: smoke tests y suite core antes de tocar modulos amplios.

### Riesgo 4: mantener secretos y defaults inseguros durante el saneo

- Impacto: alto
- Mitigacion: ejecutar SAN-070 temprano, no al final.

## Matriz Prioridad vs Impacto

### Critica

- SAN-001
- SAN-002
- SAN-003
- SAN-010
- SAN-020
- SAN-021
- SAN-030
- SAN-031
- SAN-040
- SAN-041
- SAN-050
- SAN-051
- SAN-070
- SAN-080
- SAN-081

### Alta

- SAN-011
- SAN-022
- SAN-032
- SAN-033
- SAN-042
- SAN-043
- SAN-052
- SAN-060
- SAN-062
- SAN-071
- SAN-072
- SAN-082
- SAN-090

### Media

- SAN-061
- SAN-091

## Criterios De Cierre Del Saneo

- `main.py` arranca con configuracion valida.
- `initialize_api()` arranca sin incompatibilidades de firma.
- login, insercion y consulta de datos funcionan.
- auth y scope usan `UsuarioScope`.
- no hay referencias activas a campos inexistentes del ORM.
- no hay secretos reales en configuracion versionada.
- la suite core de tests pasa en CI.
- el README principal refleja el estado real.

## Proximo Paso Recomendado

Ejecutar primero una "ola 1" enfocada en:

- SAN-010
- SAN-020
- SAN-021
- SAN-030
- SAN-031
- SAN-040
- SAN-041

Sin eso, cualquier arreglo en endpoints o tests sera inestable.
