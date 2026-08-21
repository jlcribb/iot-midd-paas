# M5.6 governed reproducibility demonstration

This is a development-only, cleanup-safe proof over the M5.1–M5.5 runtime. It
does not introduce simulation features or operational side effects.

`scripts/governed_reproducibility_demo.py` creates one marked project, an
operator membership for the configured real OAuth identity, a threshold policy
with an actionable frozen binding, and a separate recommendation-only policy.
It never creates sessions or runs: those must be created through
`/control/simulations` while signed in with OAuth.

Run inside the canonical Compose runtime:

```bash
docker compose -f infra/containers/docker-compose.yaml exec simulation-replay-runner \
  bash -lc 'PYTHONPATH=/app/src:/app/apps/parametric-control-engine/src python /app/scripts/governed_reproducibility_demo.py prepare'
```

The primary policy uses setpoint `22` and tolerance `3`; the canonical dataset
`20, 22, 24, 26` therefore produces three holds and one actionable
recommendation. After its session is READY, `mutate-live` changes the live
setpoint to `100`; a second run must still follow the frozen snapshot.

```bash
python /app/scripts/governed_reproducibility_demo.py mutate-live
python /app/scripts/governed_reproducibility_demo.py evidence
python /app/scripts/governed_reproducibility_demo.py restore-live
python /app/scripts/governed_reproducibility_demo.py cleanup
```

The cleanup path first verifies the exact namespace marker and deletes only
this fixture's simulations, runs, results, events, policies, assets, sector,
membership and project. It does not inspect, consume or purge legacy queues.
