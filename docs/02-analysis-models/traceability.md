# Analysis traceability

| Analysis concern | Primary evidence | Deterministic output |
|---|---|---|
| Process structure | `case/sources/as-is-process.json` | step diagnostics and issue tags |
| Queue intensity | `case/operations/process-instances.jsonl` | average wait per case by step |
| Rework | process events | rework-event counts |
| Ownership | process step owners and issue tags | ownership findings |
| Controls | `case/sources/business-rules.json` | mandatory-control traceability |
| Baseline KPIs | `case/expected/baseline-kpis.json` | comparison baseline |

`case/answer-key/known-bottlenecks.json` is intentionally excluded from runtime analysis and remains evaluation-only evidence.
