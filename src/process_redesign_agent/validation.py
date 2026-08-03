from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from process_redesign_agent.generator import CASE_VERSION, INSTANCE_COUNT, check_generated_case
from process_redesign_agent.io import load_instances, load_json, sha256_bytes, sha256_file
from process_redesign_agent.metrics import calculate_baseline_metrics, load_role_rates


class CaseValidationError(ValueError):
    """Raised when the frozen public case violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CaseValidationError(message)


def _validate_process_graph(process_source: dict[str, Any]) -> None:
    step_items = process_source["steps"]
    step_ids = {str(item["step_id"]) for item in step_items}
    edges = process_source["edges"]
    adjacency: dict[str, set[str]] = {step_id: set() for step_id in step_ids}
    incoming: dict[str, int] = {step_id: 0 for step_id in step_ids}
    for edge in edges:
        source = str(edge["from"])
        target = str(edge["to"])
        _require(source in step_ids and target in step_ids, f"process edge references unknown step: {source}->{target}")
        _require(source != target, f"process self-loop is not allowed: {source}")
        adjacency[source].add(target)
        incoming[target] += 1

    starts = sorted(step_id for step_id, count in incoming.items() if count == 0)
    _require(starts == ["intake_receive"], f"unexpected process start steps: {starts}")
    ends = sorted(step_id for step_id, targets in adjacency.items() if not targets)
    _require(ends == ["customer_notification"], f"unexpected process end steps: {ends}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> None:
        _require(step_id not in visiting, f"process graph cycle detected at {step_id}")
        if step_id in visited:
            return
        visiting.add(step_id)
        for target in adjacency[step_id]:
            visit(target)
        visiting.remove(step_id)
        visited.add(step_id)

    visit("intake_receive")
    _require(visited == step_ids, f"unreachable process steps: {sorted(step_ids - visited)}")


def verify_repository_case(repo_root: Path) -> dict[str, Any]:
    case_root = repo_root / "case"
    role_source = load_json(case_root / "sources/roles-and-rates.json")
    process_source = load_json(case_root / "sources/as-is-process.json")
    rules_source = load_json(case_root / "sources/business-rules.json")
    constraints = load_json(case_root / "sources/constraints-and-targets.json")
    bottlenecks = load_json(case_root / "answer-key/known-bottlenecks.json")
    manifest = load_json(case_root / "manifest.json")
    expected = load_json(case_root / "expected/baseline-kpis.json")
    instances = load_instances(case_root / "operations/process-instances.jsonl")

    _require(manifest["status"] == "FROZEN", "manifest must be FROZEN")
    _require(manifest["case_version"] == CASE_VERSION, "manifest case version mismatch")
    _require(len(instances) == INSTANCE_COUNT, f"expected {INSTANCE_COUNT} instances")
    _require(len({item.instance_id for item in instances}) == INSTANCE_COUNT, "instance IDs must be unique")
    _require(Counter(item.received_day for item in instances) == Counter({day: 8 for day in range(1, 31)}), "volume must be eight instances on each of 30 business days")

    roles = {str(item["role_id"]) for item in role_source["roles"]}
    steps = {str(item["step_id"]) for item in process_source["steps"]}
    controls = {str(item["control_id"]) for item in rules_source["mandatory_controls"]}
    _require(len(roles) == len(role_source["roles"]), "role IDs must be unique")
    _require(len(steps) == len(process_source["steps"]), "step IDs must be unique")
    _require(len(controls) == len(rules_source["mandatory_controls"]), "control IDs must be unique")
    _validate_process_graph(process_source)
    for role in role_source["roles"]:
        rate = float(role["synthetic_hourly_cost_usd"])
        _require(rate >= 0, f"negative role rate: {role['role_id']}")
        if role["role_id"] == "system":
            _require(rate == 0, "system role rate must be zero")
        else:
            _require(rate > 0, f"human role rate must be positive: {role['role_id']}")
    for step in process_source["steps"]:
        owner = str(step["default_owner_role_id"])
        _require(owner in roles or owner == "VARIABLE", f"unknown default process owner: {owner}")
        if owner == "VARIABLE":
            _require(step["step_id"] == "exception_resolution", "only exception resolution may have variable ownership")
    _require(int(constraints["baseline"]["instance_count"]) == INSTANCE_COUNT, "constraint instance count mismatch")

    allowed_exceptions = {"MISSING_DOCUMENT", "DATA_MISMATCH", "SANCTIONS_FALSE_POSITIVE"}
    allowed_control_statuses = {"PASS", "MISSING"}
    allowed_outcomes = {"COMPLETED", "REWORKED"}
    for instance in instances:
        _require(instance.case_version == CASE_VERSION, f"case version mismatch in {instance.instance_id}")
        _require(instance.risk_tier in {"STANDARD", "MEDIUM", "HIGH"}, f"unknown risk tier in {instance.instance_id}")
        _require(set(instance.exception_reasons).issubset(allowed_exceptions), f"unknown exception reason in {instance.instance_id}")
        _require(set(instance.control_results.values()).issubset(allowed_control_statuses), f"unknown control status in {instance.instance_id}")
        _require(all(event.outcome in allowed_outcomes for event in instance.events), f"unknown event outcome in {instance.instance_id}")
        _require(all(event.step_id in steps for event in instance.events), f"unknown process step in {instance.instance_id}")
        _require(all(event.role_id in roles for event in instance.events), f"unknown role in {instance.instance_id}")
        _require(set(instance.control_results).issubset(controls), f"unknown control in {instance.instance_id}")
        event_steps = [event.step_id for event in instance.events]
        _require(event_steps[:5] == ["intake_receive", "crm_rekey", "document_validation", "compliance_screening", "risk_review"], f"invalid prefix in {instance.instance_id}")
        _require(event_steps[-2:] == ["account_activation", "customer_notification"], f"invalid suffix in {instance.instance_id}")
        _require(("exception_resolution" in event_steps) == bool(instance.exception_reasons), f"exception path mismatch in {instance.instance_id}")
        _require(instance.control_results["C-01"] == "PASS", f"identity control failed in {instance.instance_id}")
        _require(instance.control_results["C-02"] == "PASS", f"screening control failed in {instance.instance_id}")
        if instance.risk_tier == "HIGH":
            _require(instance.control_results.get("C-03") == "PASS", f"high-risk approval missing in {instance.instance_id}")
        if instance.exception_reasons:
            _require(instance.control_results.get("C-04") == "PASS", f"exception control missing in {instance.instance_id}")

    actual_metrics = calculate_baseline_metrics(
        instances,
        load_role_rates(role_source),
        int(constraints["baseline"]["sla_working_minutes"]),
    )
    _require(actual_metrics == expected["metrics"], "calculated baseline metrics differ from the frozen answer key")

    manifest_files = manifest["files"]
    _require(manifest["file_count"] == len(manifest_files), "manifest file_count mismatch")
    manifested_paths = {str(entry["path"]) for entry in manifest_files}
    actual_case_paths = {
        path.relative_to(repo_root).as_posix()
        for path in case_root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    _require(manifested_paths == actual_case_paths, "manifest must cover every and only non-manifest case file")
    for entry in manifest_files:
        target = repo_root / entry["path"]
        _require(target.is_file(), f"manifest file missing: {entry['path']}")
        _require(target.stat().st_size == entry["bytes"], f"manifest byte count mismatch: {entry['path']}")
        _require(sha256_file(target) == entry["sha256"], f"manifest digest mismatch: {entry['path']}")

    bottleneck_ids = [item["bottleneck_id"] for item in bottlenecks["bottlenecks"]]
    _require(len(bottleneck_ids) == len(set(bottleneck_ids)), "bottleneck IDs must be unique")
    for item in bottlenecks["bottlenecks"]:
        _require(item["step_id"] in steps, f"bottleneck references unknown step: {item['bottleneck_id']}")
        for ref in item["evidence_refs"]:
            _require((repo_root / ref["path"]).is_file(), f"bottleneck evidence file missing: {ref['path']}")

    drift = check_generated_case(repo_root)
    _require(not drift, f"generated case drift: {', '.join(drift)}")
    manifest_bytes = (case_root / "manifest.json").read_bytes()
    return {
        "instance_count": len(instances),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "average_cycle_minutes": actual_metrics["time"]["average_cycle_minutes"],
        "p90_cycle_minutes": actual_metrics["time"]["p90_cycle_minutes"],
        "sla_attainment_rate": actual_metrics["time"]["sla_attainment_rate"],
    }
