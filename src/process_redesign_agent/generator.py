
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from process_redesign_agent.io import canonical_json_bytes, canonical_jsonl_bytes, load_json, sha256_file
from process_redesign_agent.metrics import calculate_baseline_metrics, load_role_rates
from process_redesign_agent.models import ProcessInstance

CASE_SEED = 20260803
CASE_VERSION = "atlasbridge-onboarding-as-is-v1.0.0"
GENERATOR_VERSION = "1.0.0"
INSTANCE_COUNT = 240


def _event(
    sequence: int,
    step_id: str,
    role_id: str,
    service_minutes: int,
    wait_minutes: int,
    outcome: str = "COMPLETED",
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "role_id": role_id,
        "sequence": sequence,
        "service_minutes": service_minutes,
        "step_id": step_id,
        "wait_minutes": wait_minutes,
    }


def build_instance_records() -> list[dict[str, Any]]:
    rng = random.Random(CASE_SEED)
    records: list[dict[str, Any]] = []
    for index in range(1, INSTANCE_COUNT + 1):
        risk_draw = rng.random()
        risk_tier = "STANDARD" if risk_draw < 0.65 else ("MEDIUM" if risk_draw < 0.90 else "HIGH")
        missing_document = rng.random() < 0.18
        data_mismatch = rng.random() < 0.12
        sanctions_false_positive = rng.random() < 0.05

        exception_reasons: list[str] = []
        if missing_document:
            exception_reasons.append("MISSING_DOCUMENT")
        if data_mismatch:
            exception_reasons.append("DATA_MISMATCH")
        if sanctions_false_positive:
            exception_reasons.append("SANCTIONS_FALSE_POSITIVE")
        has_exception = bool(exception_reasons)
        audit_missing = rng.random() < (0.06 + (0.07 if has_exception else 0.0))

        events: list[dict[str, Any]] = []
        events.append(_event(1, "intake_receive", "intake_specialist", rng.randint(12, 22), rng.randint(15, 90)))
        events.append(_event(2, "crm_rekey", "onboarding_analyst", rng.randint(10, 18), rng.randint(10, 60)))
        document_touch = rng.randint(18, 35) + (rng.randint(15, 35) if missing_document else 0)
        document_wait = rng.randint(80, 300) + (rng.randint(60, 180) if missing_document else 0)
        events.append(
            _event(
                3,
                "document_validation",
                "onboarding_analyst",
                document_touch,
                document_wait,
                "REWORKED" if missing_document else "COMPLETED",
            )
        )
        events.append(_event(4, "compliance_screening", "compliance_analyst", rng.randint(10, 18), rng.randint(60, 240)))

        if risk_tier == "STANDARD":
            risk_service, risk_wait = rng.randint(8, 18), rng.randint(30, 120)
        elif risk_tier == "MEDIUM":
            risk_service, risk_wait = rng.randint(15, 30), rng.randint(90, 240)
        else:
            risk_service, risk_wait = rng.randint(25, 45), rng.randint(240, 600)
        events.append(_event(5, "risk_review", "risk_manager", risk_service, risk_wait))

        next_sequence = 6
        if has_exception:
            if sanctions_false_positive:
                owner = "compliance_analyst"
            elif data_mismatch and rng.random() < 0.50:
                owner = "intake_specialist"
            else:
                owner = "onboarding_analyst"
            events.append(
                _event(
                    next_sequence,
                    "exception_resolution",
                    owner,
                    rng.randint(25, 60),
                    rng.randint(300, 1200),
                )
            )
            next_sequence += 1

        events.append(_event(next_sequence, "account_activation", "system", rng.randint(5, 10), rng.randint(30, 180)))
        events.append(_event(next_sequence + 1, "customer_notification", "support_specialist", rng.randint(4, 8), rng.randint(10, 60)))

        controls = {
            "C-01": "PASS",
            "C-02": "PASS",
            "C-05": "MISSING" if audit_missing else "PASS",
        }
        if risk_tier == "HIGH":
            controls["C-03"] = "PASS"
        if has_exception:
            controls["C-04"] = "PASS"

        records.append(
            {
                "case_version": CASE_VERSION,
                "control_results": controls,
                "exception_reasons": exception_reasons,
                "instance_id": f"AB-ONB-{index:04d}",
                "received_day": ((index - 1) // 8) + 1,
                "risk_tier": risk_tier,
                "events": events,
            }
        )
    return records


def expected_metric_document(repo_root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    roles = load_json(repo_root / "case/sources/roles-and-rates.json")
    constraints = load_json(repo_root / "case/sources/constraints-and-targets.json")
    instances = [ProcessInstance.from_dict(record) for record in records]
    metrics = calculate_baseline_metrics(
        instances,
        load_role_rates(roles),
        int(constraints["baseline"]["sla_working_minutes"]),
    )
    return {
        "case_version": CASE_VERSION,
        "calculator_contract": {
            "cost_basis": "service minutes multiplied by synthetic role rate; wait time has no labor cost",
            "cycle_time": "sum of sequential service and wait minutes",
            "percentile_method": "nearest-rank",
            "rounding": "four decimal places, half up",
        },
        "generator_version": GENERATOR_VERSION,
        "metrics": metrics,
        "status": "FROZEN_EXPECTED_RESULT",
    }


def generated_bytes(repo_root: Path) -> dict[Path, bytes]:
    records = build_instance_records()
    return {
        Path("case/operations/process-instances.jsonl"): canonical_jsonl_bytes(records),
        Path("case/expected/baseline-kpis.json"): canonical_json_bytes(
            expected_metric_document(repo_root, records)
        ),
    }


def build_manifest(repo_root: Path) -> dict[str, Any]:
    case_root = repo_root / "case"
    files: list[dict[str, Any]] = []
    for path in sorted(case_root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        relative = path.relative_to(repo_root).as_posix()
        files.append(
            {
                "bytes": path.stat().st_size,
                "path": relative,
                "sha256": sha256_file(path),
            }
        )
    return {
        "case_id": "AB-ONBOARDING-REDESIGN-001",
        "case_version": CASE_VERSION,
        "data_classification": "SYNTHETIC_PUBLIC",
        "file_count": len(files),
        "files": files,
        "frozen_at_utc": "2026-08-03T09:00:00Z",
        "generator": {
            "instance_count": INSTANCE_COUNT,
            "name": "process_redesign_agent.generator",
            "seed": CASE_SEED,
            "version": GENERATOR_VERSION,
        },
        "licence": "CC-BY-4.0",
        "status": "FROZEN",
    }


def write_generated_case(repo_root: Path) -> None:
    for relative, content in generated_bytes(repo_root).items():
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    manifest_path = repo_root / "case/manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(build_manifest(repo_root)))


def check_generated_case(repo_root: Path) -> list[str]:
    mismatches: list[str] = []
    for relative, expected in generated_bytes(repo_root).items():
        target = repo_root / relative
        if not target.exists() or target.read_bytes() != expected:
            mismatches.append(relative.as_posix())
    expected_manifest = canonical_json_bytes(build_manifest(repo_root))
    manifest_path = repo_root / "case/manifest.json"
    if not manifest_path.exists() or manifest_path.read_bytes() != expected_manifest:
        mismatches.append("case/manifest.json")
    return mismatches
