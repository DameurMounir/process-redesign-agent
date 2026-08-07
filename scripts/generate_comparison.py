from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.redesign import build_comparison, validate_comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = build_comparison(ROOT)
    validate_comparison(value)
    expected = json.dumps(value, indent=2, sort_keys=True) + "\n"
    target = ROOT / "design" / "expected" / "default-comparison.json"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            print("FAIL: default comparison drifted", file=sys.stderr)
            return 1
        print("PASS: default comparison is byte-stable")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(expected, encoding="utf-8")
    print(f"PASS: wrote {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
