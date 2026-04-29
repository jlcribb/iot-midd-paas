# ADR-001 Repository Architecture

Fecha: 2026-04-20

## Estado

Aprobado para la reorganizacion incremental del repo.

## Contexto

El repositorio contiene varias capas arquitectonicas superpuestas:

- runtime Python para ingestión, MQTT, storage y procesos IoT;
- API Python historica;
- `core_backend` Python con dominio operacional moderno;
- backend/UI Next.js con el mismo dominio operacional;
- DTE;
- infraestructura local y documentacion historica mezclada.

El principal problema es la duplicacion del dominio operacional y la falta de una estructura de repo alineada con la arquitectura real del sistema.

## Decision

### 1. Python como runtime IoT oficial

Python queda como base oficial para:

- ingestion;
- MQTT;
- storage;
- backend IoT processes;
- migraciones;
- integracion futura con cognitive core y DTE.

### 2. Next.js como dominio operacional oficial

Next.js queda como implementacion oficial del dominio operacional:

- projects;
- sectors;
- locations;
- assets;
- topology;
- provisioning;
- canvas/UI.

### 3. Legacy y transicion

- `src/iot_middleware/api` se clasifica como `legacy`.
- `src/iot_middleware/core_backend` se clasifica como `transition`.
- `containers/admin` se clasifica como `transition`.
- `containers/dashboard` se clasifica como `experimental`.

Condicion operativa actual:

- `core_backend` no debe exponerse como superficie normal del admin;
- su exposicion HTTP queda aislada bajo `/api/transition/core-backend/*`.

### 4. Direccion futura del producto

El repo debe reservar estructura explicita para:

- `apps/cognitive-core/`
- `apps/parametric-control-engine/`
- `apps/dte/`

## Consecuencias

### Positivas

- una sola implementacion oficial del dominio operacional;
- mejor mapeo entre arquitectura y codigo;
- separacion mas clara entre runtime IoT, legacy y futuro cognitivo;
- reorganizacion incremental sin romper el baseline.

### Negativas o costos

- durante la transicion seguiran coexistiendo rutas viejas y nuevas;
- el retiro de `core_backend` requerira una matriz fina de equivalencias;
- el repo seguira temporalmente con entrypoints redundantes hasta completar la mudanza.

## Criterio de aplicacion

Toda reorganizacion futura debe respetar:

- no agregar features durante el refactor;
- no retirar componentes sin clasificarlos;
- no romper el baseline Python ni la suite de `next-backend`;
- documentar cada movimiento relevante.
