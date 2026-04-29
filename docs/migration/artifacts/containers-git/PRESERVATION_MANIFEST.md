# Containers Git Preservation Manifest

Fecha: 2026-04-20

## Embedded Git state preserved

- Nested repository path: `containers/`
- Nested branch: `main`
- Nested HEAD: `2480767d0ade0d365f60f6bb8312a27aa1f810c3`
- Nested remote:
  - `origin https://github.com/jlcribb/middleware_iot_mqtt_db.git`

## Root repository state before normalization

- Root HEAD before normalization:
  - `2319b4d9238d9966ba1776d3a470498cf673f2cc`
- Root gitlink entry for `containers` before normalization:
  - `160000 2480767d0ade0d365f60f6bb8312a27aa1f810c3 0 containers`

## Preservation artifacts created

- `containers-history.bundle`
- `containers-dotgit-backup.tar.gz`
- `nested-status.txt`
- `nested-remote.txt`
- `nested-head.txt`
- `nested-branch.txt`
- `nested-tracked-files.txt`
- `root-head-before-normalization.txt`
- `root-gitlink-before-normalization.txt`

## Notes

- The embedded `.git` directory from `containers/` was preserved before normalization.
- The root repository now tracks `containers/` as regular files instead of a gitlink.
- No internal paths under `containers/*` were moved in this step.
