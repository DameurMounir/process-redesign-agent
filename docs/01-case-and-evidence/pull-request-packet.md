# Pull request packet — Milestone 01

## Proposed title

`Milestone 01: Freeze the synthetic AS-IS case and evidence baseline`

## Purpose

Establish the public-safe AtlasBridge onboarding baseline before any process
analysis or TO-BE recommendation is implemented.

## Bounded changes

- Added six human-authored synthetic source records covering process, roles,
  rules, stakeholder needs, constraints, and assumptions.
- Added 240 deterministic process instances generated from seed `20260803`.
- Added a frozen deterministic KPI answer key and six labeled bottlenecks for
  future evaluation.
- Added SHA-256 provenance, a context diagram, traceability, and validation
  documentation.
- Hardened process-graph, control, event, tamper, and manifest validation.

## Exact local validation

```text
verify_case.py                         PASS
case generation drift                 PASS
unittest                              14 PASS
public-boundary scan                  50 tracked files PASS
Python compileall                     PASS
manifest SHA-256                      a1d27b21a61aa5ac359ad6c760e5cd8abb04693402dbb58b0110708437d6f30e
```

GitHub Actions must still validate the exact pushed head on Python 3.12 and 3.13
before merge. This packet does not claim remote CI success.

## Human decision point

Merge only after confirming that the fictional case is understandable, the
baseline assumptions are acceptable for demonstration, and no TO-BE option has
been silently preselected.

## Not included

No bottleneck-analysis agent, no scenario engine, no model adapter, no preferred
option, no working UI, no external write, no deployment, and no public release.
