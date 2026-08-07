from __future__ import annotations

import argparse
import json
from pathlib import Path

from process_redesign_agent.analysis import build_as_is_analysis, validate_analysis
from process_redesign_agent.decision import create_comparison_run, export_run, select_option, show_run
from process_redesign_agent.redesign import build_comparison, validate_comparison
from process_redesign_agent.validation import verify_repository_case


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="process-redesign-agent", description="Evidence-grounded process redesign with deterministic controls and human selection.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-case", help="Verify the frozen synthetic case")
    sub.add_parser("analyze", help="Build the evidence-linked AS-IS analysis")
    sub.add_parser("compare", help="Print the default three-option comparison")

    start = sub.add_parser("start-review", help="Create a digest-bound local comparison run")
    start.add_argument("--run-id", required=True)
    show = sub.add_parser("show", help="Show a local comparison run")
    show.add_argument("--run-id", required=True)
    select = sub.add_parser("select", help="Record an explicit human selection")
    select.add_argument("--run-id", required=True)
    select.add_argument("--option", required=True)
    select.add_argument("--reviewer", required=True)
    select.add_argument("--expected-digest", required=True)
    select.add_argument("--rationale", required=True)
    export = sub.add_parser("export", help="Export a human-selected run to JSON, Markdown and HTML")
    export.add_argument("--run-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = args.repo.resolve()
    if args.command == "verify-case":
        summary = verify_repository_case(repo)
        print(f"PASS: frozen process case verified ({summary['instance_count']} instances, manifest {summary['manifest_sha256'][:12]}...)")
        return 0
    if args.command == "analyze":
        value = build_as_is_analysis(repo)
        validate_analysis(value)
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0
    if args.command == "compare":
        value = build_comparison(repo)
        validate_comparison(value)
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0
    if args.command == "start-review":
        run = create_comparison_run(repo, args.run_id)
        print(json.dumps({"run_id": run["run_id"], "status": run["status"], "comparison_digest": run["comparison_digest"], "top_scoring_candidate": run["comparison"]["top_scoring_candidate"]}, indent=2))
        return 0
    if args.command == "show":
        print(json.dumps(show_run(repo, args.run_id), indent=2, sort_keys=True))
        return 0
    if args.command == "select":
        run = select_option(repo, args.run_id, args.option, args.reviewer, args.expected_digest, args.rationale)
        print(json.dumps({"run_id": run["run_id"], "status": run["status"], "selected_option": run["decision"]["option_id"]}, indent=2))
        return 0
    if args.command == "export":
        print(export_run(repo, args.run_id))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")
