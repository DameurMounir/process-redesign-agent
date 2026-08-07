from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pkl", ".pickle", ".pem", ".key"}
FORBIDDEN_NAMES = {".env", "id_rsa", "id_ed25519"}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic password assignment": re.compile(r"(?i)(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [REPO_ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"forbidden tracked file: {relative}")
            continue
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{label} pattern in {relative}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"PASS: {len(tracked_files())} tracked files satisfy the synthetic public boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
