from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_instances(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def analysis_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _severity(wait_minutes: float, tags: set[str]) -> str:
    if {"INCOMPLETE_AUDIT_EVIDENCE", "LONG_QUEUE", "UNCLEAR_OWNERSHIP"} & tags and wait_minutes >= 100:
        return "CRITICAL"
    if wait_minutes >= 150 or {"DUPLICATE_DATA_ENTRY", "NO_END_TO_END_OWNER"} & tags:
        return "HIGH"
    if wait_minutes >= 75 or tags:
        return "MEDIUM"
    return "LOW"


def _root_cause(tags: set[str]) -> str:
    rules = [
        ("DUPLICATE_DATA_ENTRY", "Customer information is captured more than once instead of being reused."),
        ("REWORK", "Completeness defects are discovered after intake, causing late rework and another queue cycle."),
        ("SERIAL_CHECK", "Independent checks are sequenced serially even when their required inputs are already available."),
        ("UNCLEAR_OWNERSHIP", "Exception ownership is variable instead of being assigned to one accountable case owner."),
        ("NO_END_TO_END_OWNER", "Responsibility changes between queues without one visible end-to-end case owner."),
        ("INCOMPLETE_AUDIT_EVIDENCE", "Activation is not deterministically gated on a complete evidence bundle."),
        ("MANUAL_NOTIFICATION", "A low-value manual handoff remains after activation."),
        ("QUEUE", "A shared work queue accumulates waiting time faster than service time."),
    ]
    for tag, explanation in rules:
        if tag in tags:
            return explanation
    return "Observed delay is measurable, but the frozen evidence does not support a stronger causal claim."


def build_as_is_analysis(repo: Path) -> dict[str, Any]:
    case = repo / "case"
    process = _load_json(case / "sources" / "as-is-process.json")
    rules = _load_json(case / "sources" / "business-rules.json")
    stakeholders = _load_json(case / "sources" / "stakeholder-needs.json")
    baseline = _load_json(case / "expected" / "baseline-kpis.json")
    instances = _load_instances(case / "operations" / "process-instances.jsonl")
    step_defs = {item["step_id"]: item for item in process["steps"]}

    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"service": 0.0, "wait": 0.0, "visits": 0.0, "rework": 0.0})
    for instance in instances:
        for event in instance["events"]:
            bucket = totals[event["step_id"]]
            bucket["service"] += float(event["service_minutes"])
            bucket["wait"] += float(event["wait_minutes"])
            bucket["visits"] += 1
            if str(event["outcome"]).upper() in {"REWORKED", "REWORK", "RETRY"}:
                bucket["rework"] += 1

    count = len(instances)
    diagnostics: list[dict[str, Any]] = []
    for step_id, definition in step_defs.items():
        bucket = totals[step_id]
        tags = set(definition.get("current_issue_tags", []))
        avg_service = round(bucket["service"] / count, 4)
        avg_wait = round(bucket["wait"] / count, 4)
        diagnostics.append(
            {
                "step_id": step_id,
                "step_name": definition["name"],
                "owner_role_id": definition["default_owner_role_id"],
                "issue_tags": sorted(tags),
                "average_service_minutes_per_case": avg_service,
                "average_wait_minutes_per_case": avg_wait,
                "wait_to_service_ratio": round(avg_wait / avg_service, 4) if avg_service else None,
                "visits": int(bucket["visits"]),
                "rework_events": int(bucket["rework"]),
                "severity": _severity(avg_wait, tags),
                "root_cause_hypothesis": _root_cause(tags),
                "evidence_refs": [
                    {"path": "case/sources/as-is-process.json", "locator": f"step_id={step_id}"},
                    {"path": "case/operations/process-instances.jsonl", "locator": f"events[*].step_id={step_id}"},
                ],
            }
        )

    diagnostics.sort(key=lambda item: (-item["average_wait_minutes_per_case"], item["step_id"]))
    bottlenecks = [item for item in diagnostics if item["severity"] in {"CRITICAL", "HIGH", "MEDIUM"}]
    ownership = [
        {
            "step_id": item["step_id"],
            "owner_role_id": item["owner_role_id"],
            "finding": item["root_cause_hypothesis"],
        }
        for item in diagnostics
        if item["owner_role_id"] == "VARIABLE" or "NO_END_TO_END_OWNER" in item["issue_tags"]
    ]

    controls = [
        {
            "control_id": control["control_id"],
            "name": control["name"],
            "applies_when": control["applies_when"],
            "design_requirement": control["rule"],
            "status": "MANDATORY_FOR_EVERY_FUTURE_OPTION",
            "evidence_ref": {"path": "case/sources/business-rules.json", "locator": f"control_id={control['control_id']}"},
        }
        for control in rules["mandatory_controls"]
    ]

    result: dict[str, Any] = {
        "analysis_version": "2.0.0",
        "case_version": baseline["case_version"],
        "method": "transparent deterministic aggregation plus issue-tag interpretation; evaluation answer key is not read",
        "baseline_summary": baseline["metrics"],
        "step_diagnostics": diagnostics,
        "bottlenecks": bottlenecks,
        "ownership_findings": ownership,
        "mandatory_control_traceability": controls,
        "stakeholder_source": {
            "path": "case/sources/stakeholder-needs.json",
            "stakeholder_count": len(stakeholders.get("stakeholders", [])),
        },
        "decision_boundary": "Analysis may rank evidence-supported problems. It cannot select a future process.",
    }
    return result


def validate_analysis(value: dict[str, Any]) -> None:
    if not value.get("bottlenecks"):
        raise ValueError("analysis must contain at least one bottleneck")
    if len(value.get("mandatory_control_traceability", [])) < 1:
        raise ValueError("mandatory controls must be traceable")
    text = json.dumps(value, sort_keys=True)
    if "answer-key" in text:
        raise ValueError("runtime analysis must not reference the evaluation answer key")
    for finding in value["bottlenecks"]:
        if not finding.get("evidence_refs"):
            raise ValueError(f"finding {finding.get('step_id')} has no evidence")
        if finding.get("severity") not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError("invalid severity")


def write_analysis(repo: Path, output: Path) -> dict[str, Any]:
    value = build_as_is_analysis(repo)
    validate_analysis(value)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
    return value
