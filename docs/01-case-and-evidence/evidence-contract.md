# Evidence and calculation contract

## Evidence classes

| Class | Authority |
|---|---|
| Human-authored synthetic source | Defines process, roles, rules, constraints, needs, and assumptions |
| Generated synthetic operations | Supplies reproducible event-level duration, routing, quality, and control observations |
| Frozen expected result | Tests the deterministic calculator; never provided to a runtime model |
| Locked answer key | Tests future bottleneck recall; never presented as model input |
| Manifest | Binds every case file to a byte count and SHA-256 digest |

## KPI definitions

- **Cycle time:** sum of sequential service and wait minutes in one instance.
- **Touch time:** sum of service minutes.
- **Wait time:** sum of queue minutes.
- **Labor cost:** service minutes × synthetic hourly role rate; wait has no
  direct labor charge.
- **First-pass yield:** proportion with no modeled exception reason.
- **Handoffs:** changes in responsible role between consecutive events.
- **SLA attainment:** proportion with cycle time at or below 960 working minutes.
- **Control completion:** passed applicable controls divided by applicable controls.
- **P90:** nearest-rank percentile.

All displayed calculator values are rounded to four decimal places using
round-half-up. Implementation effort and change risk are deliberately excluded
from deterministic calculation because they require explicit human estimates.
