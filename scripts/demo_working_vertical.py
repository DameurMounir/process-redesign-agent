from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.decision import create_comparison_run, export_run, select_option


def main() -> int:
    run_id = "RUN-DEMO-001"
    state = ROOT / ".process-redesign" / "runs" / f"{run_id}.json"
    output = ROOT / "outputs" / run_id
    if state.exists():
        state.unlink()
    if output.exists():
        shutil.rmtree(output)
    run = create_comparison_run(ROOT, run_id)
    select_option(ROOT, run_id, "OPT-B", "demo-reviewer", run["comparison_digest"], "Selected for the synthetic demonstration after reviewing all three trade-offs.")
    target = export_run(ROOT, run_id)
    print(f"PASS: complete compare -> human select -> export journey at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
