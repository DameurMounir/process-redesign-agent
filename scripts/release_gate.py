from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
COMMANDS = [
    [PYTHON, "scripts/verify_case.py"],
    [PYTHON, "scripts/generate_case.py", "--check"],
    [PYTHON, "scripts/generate_analysis.py", "--check"],
    [PYTHON, "scripts/generate_comparison.py", "--check"],
    [PYTHON, "scripts/evaluate.py", "--check"],
    [PYTHON, "scripts/generate_public_artifacts.py", "--check"],
    [PYTHON, "-m", "compileall", "-q", "src", "scripts", "tests"],
    [PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [PYTHON, "scripts/scan_public_boundary.py"],
]


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    for command in COMMANDS:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, env=env, check=True)
    print("PASS: complete deterministic release gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
