from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from process_redesign_agent.validation import CaseValidationError, verify_repository_case


def main() -> int:
    if not (REPO_ROOT / "case/manifest.json").is_file():
        print("PASS: repository foundation contains no frozen case yet")
        return 0
    try:
        summary = verify_repository_case(REPO_ROOT)
    except (CaseValidationError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: frozen AtlasBridge onboarding case verified")
    print(f"  instances: {summary['instance_count']}")
    print(f"  average cycle minutes: {summary['average_cycle_minutes']}")
    print(f"  p90 cycle minutes: {summary['p90_cycle_minutes']}")
    print(f"  SLA attainment: {summary['sla_attainment_rate']}")
    print(f"  manifest SHA-256: {summary['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
