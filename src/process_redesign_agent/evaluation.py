from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from process_redesign_agent.redesign import build_comparison, sensitivity_profiles


def evaluate_repository(repo: Path) -> dict[str, Any]:
    comparison = build_comparison(repo)
    projections = {item["option_id"]: item for item in comparison["projections"]}
    runtime_files = ["analysis.py", "redesign.py", "advisor.py", "decision.py", "cli.py"]
    source_text = "\n".join(
        (repo / "src" / "process_redesign_agent" / name).read_text(encoding="utf-8")
        for name in runtime_files
    )
    checks = {
        "default_candidate_is_balanced": comparison["top_scoring_candidate"] == "OPT-B",
        "three_distinct_options": set(projections) == {"OPT-A", "OPT-B", "OPT-C"},
        "all_mandatory_controls_preserved": all(item["hard_controls_pass"] for item in projections.values()),
        "balanced_option_meets_targets": all(projections["OPT-B"]["target_status"].values()),
        "balanced_option_fits_soft_pilot_envelope": projections["OPT-B"]["soft_12_week_180k_constraint_pass"],
        "automation_first_exposes_soft_constraint": not projections["OPT-C"]["soft_12_week_180k_constraint_pass"],
        "runtime_does_not_reference_answer_key": "case/answer-key" not in source_text and "known-bottlenecks.json" not in source_text,
        "authority_language_is_advisory": "A human must select" in comparison["authority"],
    }
    profiles = sensitivity_profiles(repo)
    return {
        "evaluation_version": "5.0.0",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "default_ranking": comparison["ranking"],
        "sensitivity_profiles": profiles,
        "claim_boundary": "Evaluation proves behavior on one frozen synthetic case. It does not establish production forecast accuracy or realized savings.",
    }


def validate_evaluation(value: dict[str, Any]) -> None:
    if not value["all_checks_pass"]:
        failed = [name for name, passed in value["checks"].items() if not passed]
        raise ValueError(f"evaluation failed: {failed}")
