# M6 governed reproducibility demonstration

M6 is closed as a **Governed Adaptive Experimentation Layer**: it generates bounded candidate strategies, executes simulations, preserves evidence, evaluates and compares results, ranks candidates, produces governed recommendations, and records human decisions. Experimental recommendation is not operational truth; simulation evidence is not production evidence.

Run the proof from the Docker network (the replay runner is deliberately private):

```sh
docker exec -e M65_E2E_RUNNER=1 -e M65_E2E_REPORT=1 iotmw-topology-ui sh -lc 'npm test -- --run tests/integration/experiment-batch.e2e.test.ts'
```

The test emits `m6-reproducibility-manifest:v1` from PostgreSQL values, verifies ordered candidate generation from reordered JSON, batch-start replay, comparison/ranking/recommendation/review idempotency, review conflict, immutable evidence, and one audit event per semantic mutation. The fixture is persisted during verification and cleaned afterwards.

## Demonstration manifest — 2026-09-08

`project_id=00000000-0000-0000-0000-000000000001`
`search_space_id=4e360e87-4d82-4279-bdcd-51e1cedfdbd8`
`search_space_hash=a77a0dc40288e595094f8add7c73a2eaf03b438249874f9e27d69b6aa7ea6836`
`batch_id=d6a96ddc-36b2-4ba8-8666-231c3c3a981e`
`batch_hash=91c327dfafe9e36e6870b61d2ef02a54807141c3c60caa156648699ddb63089e`
`session_fingerprint=f5fa210a5e2493a3d4fb31bf47824f20da8ca8070bbc16b4893cdaae2ed9e91b`

| Item | Candidate hash | Run | Result fingerprint | Trace hash | Evaluation hash | Score | Pareto | Rank |
| ---: | --- | --- | --- | --- | --- | ---: | --- | ---: |
| 1 | `d909…69c5` | `12e5c7f7…` | `8b364e9d…6daa` | `9aef3069…54f7` | `69d766cf…c290` | .823157409 | true | 1 |
| 2 | `744e…ccfc8` | `0c79664e…` | `a8ff3512…bd18` | `74602de9…1781` | `6f0a2509…8bfc` | .823074075 | false | 2 |
| 3 | `ccee…c5aa9` | `b6c7a7c5…` | `7b3261f4…e641` | `f96333bf…6ab0` | `c90e12e…6045` | .822990742 | false | 3 |

All traces had schema v1, three points and simulated duration 2 seconds. Every evaluation had the six-profile KPI set available: tracking error, overshoot, undershoot, settling time, control effort and actuation count.

`comparison_hash=e96ecd89f9cfc976d858820ea22e1ce7a35140f59b3e209671ac0f50b0dcd328`
`ranking_hash=9664cf47518042037cc0bb4299090ed27a23e93f031b46dbc59d93dbfd3992e9`
`recommendation_hash=5563ca0a146a44bb85d8c2eaa279f956002daae4bf4edca72300b8238a94e508`
`review_hash=f165387a174e886a19097d35938180b799926ac681ca13bc98131ba0352dc6bb`

The directional comparison was `WORSE`, score delta `-0.000083334`, coverage `1`. The governed output was `UNIQUE_CANDIDATE` / `REVIEW_REQUIRED`, followed by `APPROVE_FOR_FURTHER_TESTING` under `human-review-policy:v1`; this never authorizes production.

| Invariant | Status |
| --- | --- |
| `CONTROL_RBAC_ALLOW_DEV_FALLBACK=false` | PASS |
| `REAL_ACTUATION_READY=NO` | PASS |
| `PHYSICAL_EFFECTS=false` | PASS |
| Candidate does not mutate policy | PASS |
| Recommendation does not activate policy | PASS |
| Human decision does not deploy | PASS |
| Historical evidence immutable | PASS |
| Project isolation / RBAC | PASS |
| Idempotency / reproducibility | PASS |

| Stage | System authority | Human authority | Physical effect |
| --- | --- | --- | --- |
| Candidate generation | generate | define bounds | none |
| Simulation | execute simulated | authorize setup | none |
| Evaluation / ranking | calculate / order evidence | define profile and policy | none |
| Recommendation | propose | review | none |
| Human review | record decision | decide | none |

The E2E does not use RabbitMQ or the operational outbox; RabbitMQ being present is infrastructure only. Limitations remain: simulation only, not physical closed loop; some KPIs may be unavailable in other scenarios; M6.5 orchestration is sequential; durable recovery of orphaned `RUNNING` work is pending; there is no promotion, deployment, actuation, or complete M6 UI.
