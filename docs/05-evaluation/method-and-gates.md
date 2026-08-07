# Milestone 05 — evaluation and hardening

The release gate evaluates behavior, not marketing claims. It verifies the frozen case, generated artifacts, AS-IS analysis, three-option comparison, control preservation, human-authority boundary, compilation, deterministic tests, and public-data boundary.

The default result is intentionally narrow: the balanced option is the highest-scoring candidate under the published default weights and it meets the synthetic target envelope. This is evidence about the frozen AtlasBridge case only. It is not evidence that the same option will dominate in another company, volume profile, risk appetite, cost structure, or implementation environment.

## Adversarial properties covered by tests

- unsafe run IDs cannot escape local state directories;
- stale comparison digests cannot be approved;
- an unknown option cannot be selected;
- a completed human selection cannot be silently overwritten;
- exports require a human selection;
- invalid trade-off weights are rejected;
- mandatory controls gate an option before ranking;
- runtime analysis does not consume the evaluation answer key.
