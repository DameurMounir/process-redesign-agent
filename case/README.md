# AtlasBridge onboarding redesign case

This directory is the frozen, fictional evidence baseline for the Process
Redesign Agent. It contains no disguised customer or private-company material.

## Trusted evidence

- `sources/process-brief.md`: business problem, scope, and observed symptoms.
- `sources/as-is-process.json`: current steps, ownership, and routing.
- `sources/roles-and-rates.json`: synthetic roles and hourly cost assumptions.
- `sources/business-rules.json`: mandatory controls and business rules.
- `sources/stakeholder-needs.json`: attributed fictional needs and constraints.
- `sources/constraints-and-targets.json`: baseline calculation and redesign limits.
- `operations/process-instances.jsonl`: 240 deterministic AS-IS instances.
- `expected/baseline-kpis.json`: known calculator result for those instances.
- `answer-key/known-bottlenecks.json`: labeled analysis targets kept out of runtime.
- `manifest.json`: byte count and SHA-256 for every case file except itself.

The operations dataset and KPI answer key are generated with a fixed seed. The
answer key is for evaluation and deterministic regression only; it is not a
forecast and must not be supplied to a future model adapter.
