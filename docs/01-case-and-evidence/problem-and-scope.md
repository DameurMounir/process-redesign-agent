# Milestone 01 — problem and scope

## Business question

Which future onboarding process offers the best measurable trade-off across
speed, quality, labor cost, control preservation, implementation effort, and
change risk?

## Why this is a redesign problem

The AS-IS process is not failing because one task is merely slow. It combines
repeated data capture, serial queues, fragmented ownership, variable exception
routing, and incomplete activation evidence. Optimizing only one queue could
move delay elsewhere or weaken a mandatory control.

## Milestone objective

Freeze an internally consistent, inspectable baseline before any agent proposes
solutions. This milestone therefore supplies source evidence, a deterministic
240-instance operating dataset, expected AS-IS KPI results, known analysis
labels, assumptions, and SHA-256 provenance.

## Exit gate

Milestone 01 passes only when:

- all case material is synthetic and public-safe;
- all source IDs, role IDs, step IDs, and control IDs are unique;
- every process instance validates against the AS-IS route;
- high-risk and exception controls are present when applicable;
- the deterministic calculator exactly reproduces the frozen KPI answer key;
- generated files are byte-stable from the fixed seed;
- every case file is bound by the manifest.
