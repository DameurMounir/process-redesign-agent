
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from process_redesign_agent.generator import check_generated_case, write_generated_case


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the frozen synthetic process case")
    parser.add_argument("--check", action="store_true", help="Fail rather than write when artifacts differ")
    args = parser.parse_args()
    if not (REPO_ROOT / "case/sources").is_dir():
        print("PASS: repository foundation contains no frozen case yet")
        return 0
    if args.check:
        mismatches = check_generated_case(REPO_ROOT)
        if mismatches:
            print("FAIL: generated case drift: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        print("PASS: generated process instances, KPI answer key, and manifest are byte-stable")
        return 0
    write_generated_case(REPO_ROOT)
    print("Generated frozen AtlasBridge case artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
