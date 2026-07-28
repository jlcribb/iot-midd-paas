# Topology Next Dependency Security Readiness

## Scope

- Application: `apps/topology-next`
- Date: `2026-07-28`
- Prompt: `MIDD IOT — PROMPT 014`
- Objective: reduce vulnerable dependencies without changing the published parametric-control workspace behavior

## Baseline

- `next`: `14.2.13`
- `next-auth`: `4.24.14`
- `vitest`: `2.1.8`
- Initial audit: `9` vulnerabilities
- Initial severity split: `critical=3`, `high=2`, `moderate=4`, `low=0`

Direct dependencies flagged by audit:

- `next`
- `next-auth`
- `vitest`

Relevant transitives:

- `postcss`
- `vite`
- `vite-node`
- `esbuild`
- `uuid`
- `@vitest/mocker`

## Applied hardening

Safe updates applied after compatibility review:

- `next-auth` `4.24.14` -> `4.24.15`
- `vitest` `2.1.8` -> `3.2.6`
- `vite` added and pinned as dev dependency at `6.4.3`

Resolved transitives after the update set:

- `uuid` `8.3.2` -> `11.1.1`
- `vite-node` `2.1.8` -> `3.2.4`
- `@vitest/mocker` `2.1.8` -> `3.2.6`
- `esbuild` `0.21.5` -> `0.25.12`

## Audit result after hardening

- Final audit: `2` vulnerabilities
- Final severity split: `critical=1`, `high=1`, `moderate=0`, `low=0`

Advisories removed by the intervention:

- `next-auth` advisory set affecting `<=4.24.14`
- `uuid` advisory on versions `<11.1.1`
- `vitest` critical advisories affecting `<2.1.9` and `<3.2.6`
- `vite` advisory set affecting `<=6.4.2`
- `vite-node` and `@vitest/mocker` advisories inherited from vulnerable `vite`
- `esbuild` advisory affecting `<=0.24.2`

Residual advisories:

- `next@14.2.13` remains flagged by multiple advisories, including critical middleware authorization bypass coverage in the audited range
- `postcss@8.4.31` remains transitively bundled by `next`

## Compatibility decision

### Accepted

- `next-auth@4.24.15` because it is the next patch version and preserves compatibility with `next@14`
- `vitest@3.2.6` with `vite@6.4.3` because the project uses a minimal Node test setup and validation passed without regressions

### Deferred

- `next` major upgrade was not applied in this intervention
- `next@14.2.35` was analyzed but still resolves `postcss@8.4.31`
- `next@15.5.21` was analyzed and still resolves `postcss@8.4.31`
- `npm audit` only offers `next@16.2.12` as a full fix path, which is a major upgrade and requires dedicated migration planning

## Validation summary

- `npm test`: `72 passed`
- `npm run typecheck`: `PASS`
- `npm run build`: `PASS`
- Build warnings: existing `DYNAMIC_SERVER_USAGE` on `/api/control/access`, `/api/control/audit`, `/api/control/recommendations`, `/api/control/status`
- Python focalized tests: `18 passed`
- `apps/parametric-control-engine` tests: `35 passed`
- `docker compose -f infra/containers/docker-compose.yaml config`: `PASS`
- Runtime smoke on original repo: `PASS`

## Release readiness conclusion

- Security status: `DEPENDENCY_SECURITY_BLOCKED_BY_MAJOR_UPGRADE`
- Delivery status: dependency hardening is valid for local commit and human review
- Remaining work: plan a dedicated `next` major upgrade path, re-run the same validation matrix, and only then consider publication
