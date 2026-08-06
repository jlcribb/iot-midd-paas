# Prompt 029 - Writable Operational Clone Report

## Identification

- prompt: `MIDD IOT - PROMPT 029 - Creacion controlada de clon operativo writable y preservacion de la baseline local`
- date: `2026-08-06`
- source clone: `/Users/joseluis/dev/iot-midd-paas-clean`
- operational clone: `/Users/joseluis/dev/iot-midd-paas-auth-work`
- official remote: `https://github.com/jlcribb/iot-midd-paas.git`
- final readiness: `READY_TO_RESUME_PROMPT028_IN_WRITABLE_CLONE`
- final status: `COMPLETED_WRITABLE_OPERATIONAL_CLONE_OK`

## Cause Of Block

- Prompt 027 and Prompt 028 were blocked because `/Users/joseluis/dev/iot-midd-paas-clean` was readable but not writable in this session.
- The preserved clean clone still contained the local unpublished baseline that had to be retained before any OAuth work could continue.

## Source Baseline

- active branch: `main`
- `HEAD`: `55e2af58e71896770ad65e008656fcfa3c2d0342`
- parent: `a231887f332265a4773cfb0d574de268f43f2bdf`
- `origin/main`: `a231887f332265a4773cfb0d574de268f43f2bdf`
- divergence before clone: `0 1`
- local upgrade branch: `chore/topology-next-major-upgrade`
- upgrade branch head: `f03ec4a2052f2eb855fa466f490b06c4f6fe2689`
- RC tag: `topology-next-next16-security-rc1`
- RC tag object: `6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
- RC tag target: `a231887f332265a4773cfb0d574de268f43f2bdf`

## Clone Method

- command used:

```bash
git clone --no-hardlinks \
  /Users/joseluis/dev/iot-midd-paas-clean \
  /Users/joseluis/dev/iot-midd-paas-auth-work
```

- rationale:
  - preserves the full local unpublished history
  - avoids depending only on `origin/main`
  - avoids hardlinks against the preserved source clone

## Remote And Refs

- clone-time `origin` initially pointed to the local source clone
- `origin` was corrected to:
  - `https://github.com/jlcribb/iot-midd-paas.git`
- local `origin/main` was corrected to preserve the remote publication baseline:
  - from local-clone-derived `55e2af58e71896770ad65e008656fcfa3c2d0342`
  - to `a231887f332265a4773cfb0d574de268f43f2bdf`
- correction command used:

```bash
git -C /Users/joseluis/dev/iot-midd-paas-auth-work update-ref \
  refs/remotes/origin/main \
  a231887f332265a4773cfb0d574de268f43f2bdf
```

## Branches And Tags

- local branches preserved:
  - `main`
  - `chore/topology-next-major-upgrade`
- upgrade branch upstream:
  - none
- tags preserved:
  - `control-engine-mvp-rc1.1`
  - `topology-next-next16-security-rc1`
- RC tag verification:
  - object `6f65fd4d5a1ca716fc2ffe25ee23889f71f980ea`
  - target `a231887f332265a4773cfb0d574de268f43f2bdf`

## Divergence

- new clone before this report commit:
  - `main = 55e2af58e71896770ad65e008656fcfa3c2d0342`
  - `origin/main = a231887f332265a4773cfb0d574de268f43f2bdf`
  - divergence `0 1`
- this preserves the same unpublished local commit that existed in the clean source clone

## Write Access

- the new operational clone was created successfully in a writable user path
- write probes succeeded in:
  - repository root
  - `apps/topology-next`
- operational result:
  - the new clone is suitable for subsequent writable work

## Residual And Security Checks

- confirmed absent in the new clone:
  - `apps/topology-next/.env.local`
  - `apps/topology-next/.next`
  - `apps/topology-next/node_modules`
  - `venv`
  - `docs/informe_intervencion_codex_chatgpt_2026-07-27.md`
- no secrets were copied
- no caches were copied
- no manual file copy of the worktree was performed

## Scope Limits

- no OAuth implementation was performed in this phase
- no application code was modified
- no `.env.local` was created
- no push was performed
- no tags were created, moved, or deleted
- no releases were created

## Outcome

- operational writable clone established successfully
- source clone preserved without modifications
- original repository preserved without modifications
- Prompt 028 can resume from `/Users/joseluis/dev/iot-midd-paas-auth-work`

## Next Step

- resume Prompt 028 in `/Users/joseluis/dev/iot-midd-paas-auth-work`, starting with `.env.local` ignore hardening and the OAuth preparation work that remained pending
