from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_WEIGHTS: dict[str, float] = {
    "cycle_time_improvement": 0.25,
    "sla_attainment": 0.15,
    "first_pass_yield": 0.15,
    "labor_cost_improvement": 0.10,
    "implementation_effort": 0.15,
    "change_risk": 0.20,
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def comparison_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def validate_weights(weights: dict[str, float]) -> None:
    if set(weights) != set(DEFAULT_WEIGHTS):
        raise ValueError("weights must use exactly the supported comparison dimensions")
    if any(value < 0 or value > 1 for value in weights.values()):
        raise ValueError("weights must be between zero and one")
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("weights must sum to 1.0")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def _project_option(baseline: dict[str, Any], option: dict[str, Any], mandatory_controls: set[str]) -> dict[str, Any]:
    metrics = baseline["metrics"]
    service_by_step = metrics["diagnostics"]["average_touch_minutes_by_step"]
    wait_by_step = metrics["diagnostics"]["average_wait_minutes_by_step"]

    projected_service = sum(
        float(minutes) * (1.0 - float(option["service_reduction_by_step"].get(step_id, 0.0)))
        for step_id, minutes in service_by_step.items()
    )
    projected_wait = sum(
        float(minutes) * (1.0 - float(option["wait_reduction_by_step"].get(step_id, 0.0)))
        for step_id, minutes in wait_by_step.items()
    )
    avg_cycle = projected_service + projected_wait
    base_avg_cycle = float(metrics["time"]["average_cycle_minutes"])
    ratio = avg_cycle / base_avg_cycle
    projected_p90 = float(metrics["time"]["p90_cycle_minutes"]) * ratio * float(option["tail_multiplier"])
    base_sla = float(metrics["time"]["sla_attainment_rate"])
    projected_sla = _clamp(base_sla + max(0.0, 1.0 - projected_p90 / float(metrics["time"]["p90_cycle_minutes"])) * 0.65, 0.0, 0.99)
    projected_fpy = _clamp(float(metrics["quality_and_flow"]["first_pass_yield"]) + float(option["first_pass_yield_gain"]), 0.0, 0.99)
    projected_exception = _clamp(float(metrics["quality_and_flow"]["exception_rate"]) - float(option["exception_rate_reduction"]), 0.03, 1.0)
    projected_labor = float(metrics["cost_and_capacity"]["average_labor_cost_usd"]) * projected_service / float(metrics["time"]["average_touch_minutes"])

    coverage = set(option["control_coverage"])
    hard_controls_pass = coverage == mandatory_controls
    soft_delivery_pass = int(option["implementation_weeks"]) <= 12 and float(option["implementation_cost_usd"]) <= 180000
    target = {
        "p90_cycle_minutes_maximum": projected_p90 <= 960,
        "sla_attainment_rate_minimum": projected_sla >= 0.90,
        "first_pass_yield_minimum": projected_fpy >= 0.85,
        "activation_audit_evidence_rate": hard_controls_pass,
    }

    return {
        "option_id": option["option_id"],
        "name": option["name"],
        "summary": option["summary"],
        "projected": {
            "average_touch_minutes": round(projected_service, 4),
            "average_wait_minutes": round(projected_wait, 4),
            "average_cycle_minutes": round(avg_cycle, 4),
            "p90_cycle_minutes": round(projected_p90, 4),
            "sla_attainment_rate": round(projected_sla, 4),
            "first_pass_yield": round(projected_fpy, 4),
            "exception_rate": round(projected_exception, 4),
            "average_labor_cost_usd": round(projected_labor, 4),
            "activation_audit_evidence_rate": 1.0 if hard_controls_pass else 0.0,
        },
        "implementation": {
            "weeks": int(option["implementation_weeks"]),
            "synthetic_budget_usd": float(option["implementation_cost_usd"]),
            "change_risk": float(option["change_risk"]),
        },
        "hard_controls_pass": hard_controls_pass,
        "soft_12_week_180k_constraint_pass": soft_delivery_pass,
        "target_status": target,
        "assumption_notice": "Projection is a deterministic scenario transformation of the frozen synthetic baseline, not a production forecast or realized benefit claim.",
    }


def _score(projection: dict[str, Any], baseline: dict[str, Any], weights: dict[str, float]) -> float:
    p = projection["projected"]
    b = baseline["metrics"]
    time_improvement = _clamp(1.0 - float(p["average_cycle_minutes"]) / float(b["time"]["average_cycle_minutes"]))
    labor_improvement = _clamp(1.0 - float(p["average_labor_cost_usd"]) / float(b["cost_and_capacity"]["average_labor_cost_usd"]))
    effort = _clamp(1.0 - float(projection["implementation"]["weeks"]) / 20.0)
    risk = _clamp(1.0 - float(projection["implementation"]["change_risk"]))
    score = (
        weights["cycle_time_improvement"] * time_improvement
        + weights["sla_attainment"] * float(p["sla_attainment_rate"])
        + weights["first_pass_yield"] * float(p["first_pass_yield"])
        + weights["labor_cost_improvement"] * labor_improvement
        + weights["implementation_effort"] * effort
        + weights["change_risk"] * risk
    )
    if not projection["hard_controls_pass"]:
        return 0.0
    if not projection["soft_12_week_180k_constraint_pass"]:
        score *= 0.85
    return round(score, 6)


def build_comparison(repo: Path, weights: dict[str, float] | None = None) -> dict[str, Any]:
    chosen_weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    validate_weights(chosen_weights)
    baseline = _load_json(repo / "case" / "expected" / "baseline-kpis.json")
    rules = _load_json(repo / "case" / "sources" / "business-rules.json")
    design = _load_json(repo / "design" / "options.json")
    mandatory = {item["control_id"] for item in rules["mandatory_controls"]}
    projections = [_project_option(baseline, option, mandatory) for option in design["options"]]
    for projection in projections:
        projection["tradeoff_score"] = _score(projection, baseline, chosen_weights)
    ranking = [item["option_id"] for item in sorted(projections, key=lambda item: (-float(item["tradeoff_score"]), item["option_id"]))]
    return {
        "comparison_version": "3.0.0",
        "weights": chosen_weights,
        "baseline_case_version": baseline["case_version"],
        "projections": projections,
        "ranking": ranking,
        "top_scoring_candidate": ranking[0],
        "authority": "Top scoring candidate is decision support only. A human must select or reject a future process in a later review step.",
    }


def validate_comparison(value: dict[str, Any]) -> None:
    validate_weights({key: float(val) for key, val in value["weights"].items()})
    if len(value["projections"]) < 2:
        raise ValueError("at least two future-state options are required")
    ids = [item["option_id"] for item in value["projections"]]
    if len(ids) != len(set(ids)):
        raise ValueError("option identifiers must be unique")
    if value["top_scoring_candidate"] not in ids:
        raise ValueError("candidate must reference a modeled option")
    for projection in value["projections"]:
        if not projection["hard_controls_pass"]:
            raise ValueError(f"option {projection['option_id']} violates a mandatory control")


def sensitivity_profiles(repo: Path) -> dict[str, str]:
    profiles = {
        "balanced": DEFAULT_WEIGHTS,
        "speed": {"cycle_time_improvement": 0.45, "sla_attainment": 0.20, "first_pass_yield": 0.10, "labor_cost_improvement": 0.05, "implementation_effort": 0.05, "change_risk": 0.15},
        "cost_and_change": {"cycle_time_improvement": 0.10, "sla_attainment": 0.10, "first_pass_yield": 0.10, "labor_cost_improvement": 0.20, "implementation_effort": 0.25, "change_risk": 0.25},
    }
    return {name: build_comparison(repo, weights)["top_scoring_candidate"] for name, weights in profiles.items()}
