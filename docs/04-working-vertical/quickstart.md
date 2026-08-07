# Milestone 04 — working vertical

The complete local journey is:

```bash
PYTHONPATH=src python3 -m process_redesign_agent.cli --repo . start-review --run-id RUN-001
PYTHONPATH=src python3 -m process_redesign_agent.cli --repo . show --run-id RUN-001
PYTHONPATH=src python3 -m process_redesign_agent.cli --repo . select --run-id RUN-001 --option OPT-B --reviewer mounir --expected-digest <digest> --rationale "Accepted after reviewing time, control, cost, effort, and change-risk trade-offs."
PYTHONPATH=src python3 -m process_redesign_agent.cli --repo . export --run-id RUN-001
```

The ranking is advisory. The selection command requires a human-supplied reviewer identity, rationale, and the exact comparison digest. A stale digest is rejected. The selected run exports JSON, Markdown, and a self-contained HTML decision view under ignored local output paths.
