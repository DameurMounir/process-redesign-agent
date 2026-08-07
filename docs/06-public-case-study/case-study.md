# Public case study — choosing a future onboarding process

## Decision question

**Which future process offers the best trade-off between cycle time, control preservation, operating cost, implementation effort, and change risk?**

The fictional AtlasBridge baseline contains 240 deterministic onboarding cases. The measured AS-IS process spends 89.08% of cycle time waiting, reaches its 960-working-minute SLA in only 53.75% of cases, and has a 61.67% first-pass yield.

The project analyzes that baseline without reading its evaluation-only bottleneck answer key, then models three explicit future states. Every option must preserve the five mandatory controls before it is eligible for ranking.

Under the published default weights, **OPT-B — Balanced parallel-control redesign** is the highest-scoring candidate. It combines one reusable intake record, one accountable case owner, parallel independent checks, a dedicated exception lane, evidence-bound activation, and automated notification. In the synthetic scenario it also fits the 12-week / USD 180,000 pilot envelope.

OPT-A carries less change risk but leaves too much queue time. OPT-C has the strongest modeled operating performance but exceeds the pilot envelope and carries the highest change risk. That tension is the point of the case: the system exposes trade-offs rather than hiding them behind a single optimization target.

The ranking remains advisory. A human reviewer can select OPT-A, OPT-B, or OPT-C after seeing the digest-bound comparison, provided the chosen option preserves every mandatory control. A stale comparison cannot be reused for a later decision.

None of the modeled improvements are realized savings or production forecasts. They are deterministic transformations of one frozen synthetic evidence pack.
