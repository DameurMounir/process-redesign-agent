from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.evaluation import evaluate_repository, validate_evaluation


def markdown(value: dict[str, object]) -> str:
    checks = value["checks"]
    assert isinstance(checks, dict)
    lines = ["# Evaluation result", "", "| Gate | Result |", "|---|---|"]
    for name, passed in checks.items():
        lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")
    lines += ["", f"Default ranking: `{value['default_ranking']}`", "", str(value["claim_boundary"]), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = evaluate_repository(ROOT)
    validate_evaluation(value)
    json_text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    md_text = markdown(value)
    json_target = ROOT / "evaluation" / "results" / "evaluation.json"
    md_target = ROOT / "evaluation" / "results" / "evaluation.md"
    if args.check:
        if not json_target.exists() or json_target.read_text(encoding="utf-8") != json_text:
            print("FAIL: evaluation JSON drifted", file=sys.stderr)
            return 1
        if not md_target.exists() or md_target.read_text(encoding="utf-8") != md_text:
            print("FAIL: evaluation Markdown drifted", file=sys.stderr)
            return 1
        print("PASS: evaluation results are byte-stable")
        return 0
    json_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json_text, encoding="utf-8")
    md_target.write_text(md_text, encoding="utf-8")
    print("PASS: wrote evaluation results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
