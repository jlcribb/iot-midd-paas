> Architecture Package v0.2 — Estado: `APPROVED`.
> Clase estratégica: A1 — Digital Twin Foundation. R1 resolvió el baseline: `STEP_0_GATE = PASS`. Implementación completada con advertencias no bloqueantes; véase el [informe final](GDSS-001-FINAL-REPORT.md). Este diseño conceptual se concreta mediante las migraciones 0039 y 0040 y el supertipo relacional documentado en la [reconciliación](GDSS-001-RECONCILIATION.md).
> Este documento especifica requisitos arquitectónicos aprobados; no describe capacidades GDSS implementadas.

# 1. Principio

Separar:

```text
IDENTITY
    ≠
VERSION
    ≠
LIFECYCLE EVENT
```

---

# 2. Esquema conceptual

```text
gdss_system_model_identity
        │
        └── gdss_system_model_version
                    │
                    ├── gdss_component
                    ├── gdss_variable
                    ├── gdss_parameter
                    ├── gdss_formula
                    ├── gdss_constraint
                    └── gdss_boundary

gdss_lifecycle_event
gdss_unit_definition
gdss_dimension_definition
```

R1/R2: cada tabla hija contiene `model_version_id` obligatorio, referenciado a `gdss_system_model_version`. Las referencias entre hijos deben incluir la pertenencia a la misma versión y rechazar referencias cruzadas. El plan especificará las claves y restricciones SQL concretas. No hay tablas de identidad, versión o lifecycle independientes para fórmulas (NB-04).

---

# 3. Identidad

La identidad permanece estable entre versiones.

Ejemplo:

```text
ThermalRoomModel
```

puede tener:

```text
v1
v2
v3
```

sin crear tres identidades conceptualmente independientes.

---

# 4. Versiones

Cada versión deberá tener:

```text
version_number
content_hash
created_at
created_by
lifecycle_status
```

El hash deberá derivarse de una representación canónica del contenido gobernado.

No deberá depender de:

- timestamp;
- UUID generado;
- orden incidental de serialización.

NB-01: la canonicalización distinguirá colecciones sin orden de secuencias con orden semántico. Sólo las primeras pueden normalizarse por ordenación. El plan definirá la clasificación por campo, la representación estable de referencias locales y los campos incluidos en el hash; no se ordenarán indiscriminadamente todas las listas. Los UUID y timestamps excluidos son los generados como identidad técnica y auditoría, no valores declarativos que tengan significado en el modelo.

El lifecycle y su historial se mantienen fuera del contenido hasheado. Validar deberá fijar el hash del contenido validado; las transiciones posteriores lo preservarán. Las ediciones de `DRAFT` requieren recalcularlo antes de validar. La operación de validación, congelamiento y registro de evento deberá ser atómica para evitar cambios concurrentes sobre contenido ya validado.

---

# 5. Inmutabilidad

R5: sólo `DRAFT` permite edición autorizada. Los siguientes estados conservan contenido inmutable:

```text
VALIDATED
EXPERIMENTAL
APPROVED
PUBLISHED
DEPRECATED
```

deberán ser inmutables respecto del contenido histórico.

Una corrección produce:

```text
new DRAFT successor version
```

Nunca:

```text
UPDATE frozen content
```

La protección comprende el contenido del aggregate y todos sus hijos, incluyendo procedencia, unidades/dimensiones y restricciones. Las definiciones de catálogo referenciadas deberán conservar su significado histórico; el plan fijará cómo inmovilizarlas o capturarlas en la versión. Ninguna actualización indirecta puede alterar contenido congelado.

Un sucesor tiene nuevos registros hijos asociados exclusivamente a su versión. Se preserva la referencia al predecesor para trazabilidad. El original no vuelve a `DRAFT`. Cambiar `PUBLISHED` a `DEPRECATED` sólo modifica el estado gobernado y registra el evento; no modifica contenido ni hash.

---

# 6. Lifecycle events

Cada transición produce un evento append-only.

Ejemplo:

```text
LifecycleEvent
 ├── entity
 ├── entity_version
 ├── from_status
 ├── to_status
 ├── actor
 ├── timestamp
 ├── reason
 └── metadata
```

No se reemplaza el historial.

El sujeto de las transiciones es siempre `SystemModelVersion`; sus hijos no mantienen otra máquina de estados. Cada transición y su evento deben persistirse atómicamente. `VALIDATED` tiene el significado estructural y de gobernanza definido en CONTRACTS, sin acreditación científica.

---

# 7. Publicación

`PUBLISHED` significa:

> esta versión concreta ha sido aceptada como artefacto publicado dentro de su contexto de gobernanza.

No significa:

- científicamente verdadera;
- universalmente válida;
- apta para control;
- autorizada para actuación.

---

# 8. Deprecación

`DEPRECATED` preserva íntegramente la versión.

No implica eliminación.

Los consumidores futuros deberán poder conocer qué versión la reemplaza, si existe.

---

# 9. Provenance preservation / aggregation without epistemic promotion

Una composición deberá conservar la procedencia de sus elementos.

Ejemplo:

```text
SystemModel
 ├── Formula A — LITERATURE
 ├── Formula B — EMPIRICAL
 └── Formula C — AI_PROPOSED
```

No podrá reducirse incorrectamente a:

```text
SystemModel provenance = LITERATURE
```

La procedencia compuesta deberá conservar heterogeneidad.

NB-03: la procedencia propia del modelo y la de cada hijo permanecen identificables. Una agregación no reemplaza fuentes originales ni eleva categorías por validación, aprobación o publicación.

---

# 10. Eliminación

Los artefactos publicados no deberán eliminarse mediante operaciones normales de usuario.

La estrategia concreta de retención física deberá alinearse con las políticas generales del repositorio.
