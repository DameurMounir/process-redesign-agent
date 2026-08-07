from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from process_redesign_agent.analysis import build_as_is_analysis, validate_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(build_as_is_analysis(ROOT), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    validate_analysis(json.loads(expected))
    target = ROOT / "analysis" / "as-is-analysis.json"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            print("FAIL: analysis/as-is-analysis.json drifted", file=sys.stderr)
            return 1
        print("PASS: AS-IS analysis is byte-stable")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(expected, encoding="utf-8")
    os.chmod(target, 0o644)
    print("PASS: wrote analysis/as-is-analysis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
