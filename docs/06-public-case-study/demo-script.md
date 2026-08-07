# Five-minute demonstration script

1. Open the README and show the frozen AS-IS metrics and the authority boundary.
2. Run `PYTHONPATH=src python3 scripts/generate_analysis.py --check` to prove that the AS-IS analysis is reproducible and does not depend on the answer key.
3. Run `PYTHONPATH=src python3 scripts/generate_comparison.py --check` and open `design/expected/default-comparison.json`.
4. Compare OPT-A, OPT-B, and OPT-C. Emphasize that all five mandatory controls gate eligibility before scoring.
5. Start a local review with `start-review --run-id RUN-DEMO-001` and show the returned comparison digest.
6. Explain that the top-scoring candidate is advisory only. Select an option with the exact digest and a human rationale.
7. Export the selected run and open the generated HTML decision view.
8. Finish with `PYTHONPATH=src python3 scripts/release_gate.py` and explain the boundary: this repository proves one reproducible synthetic case, not universal redesign accuracy.
