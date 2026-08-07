from __future__ import annotations

import argparse
from pathlib import Path

from process_redesign_agent.validation import verify_repository_case


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="process-redesign-agent",
        description="Controlled process-redesign portfolio workflow.",
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-case", help="Verify the frozen Milestone 01 case")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "verify-case":
        summary = verify_repository_case(args.repo.resolve())
        print(
            "PASS: frozen process case verified "
            f"({summary['instance_count']} instances, "
            f"manifest {summary['manifest_sha256'][:12]}...)"
        )
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")
