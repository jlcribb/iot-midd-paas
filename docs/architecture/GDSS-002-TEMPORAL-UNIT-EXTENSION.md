# MIDD-IOT — GDSS-002 Temporal Unit Contract Extension
## Post-closure contract extension v0.1

**Status:** `IMPLEMENTED_FOR_REVIEW`
**Baseline:** `dade8e6d490ea3adc88aac0353c2e72fee2df47b`
**Migration:** `NONE`

This extension does not rewrite the GDSS-002 closure. `GDSS_UNIT_CONVERSION_V1` remains the exact
historical default and is immutable. `GDSS_UNIT_CONVERSION_V2` is an explicit immutable successor;
callers must select a version and no runtime notion of “latest” exists.

V2 contains every V1 definition without semantic change and adds exactly:

```text
key: second
revision: 1
symbol: s
name: second
dimension: [0,0,1,0,0,0,0]
scale: 1
offset: 0
canonical_unit: second
quantity semantics: INTERVAL
affine family: false
```

`second@1` is a physical duration interval, not a calendar instant, wall-clock timestamp,
observation timestamp or device timestamp. V1 rejects it; V2 accepts it. Existing compound units
retain their definitions and satisfy `meter_per_second × second → meter` and
`cubic_meter_per_second × second → cubic_meter` dimensionally.

Evaluation input identity already includes the explicit catalog version. Consequently V1 and V2
may produce the same numeric conversion for inherited units but have distinct governed input/result
identity. Unknown versions and unit/catalog mismatches fail closed.

### Extension invariants

| ID | Statement | Status |
|---|---|---|
| GDS2-EXT-INV-01 | V1 definitions and default behavior remain immutable. | PASS |
| GDS2-EXT-INV-02 | V2 explicitly succeeds V1 and preserves every inherited definition. | PASS |
| GDS2-EXT-INV-03 | `second@1` exists in V2 and not V1. | PASS |
| GDS2-EXT-INV-04 | `second@1` has TIME dimension, scale 1, offset 0 and INTERVAL semantics. | PASS |
| GDS2-EXT-INV-05 | Catalog selection is explicit; unknown versions fail closed. | PASS |
| GDS2-EXT-INV-06 | Historical V1 evaluations remain reproducible. | PASS |
| GDS2-EXT-INV-07 | V1 compound-unit definitions are semantically identical in V2. | PASS |
| GDS2-EXT-INV-08 | Time-unit extension adds no persistence or operational dependency. | PASS |

This extension authorizes no GDSS-003 runtime implementation. P008-R2 must explicitly select
`GDSS_UNIT_CONVERSION_V2` for temporal simulation.
