from __future__ import annotations

import math
import statistics
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from process_redesign_agent.models import ProcessInstance, decimal_rate


METRIC_SCALE = Decimal("0.0001")


def _rounded(value: Decimal | float | int) -> float:
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return float(decimal_value.quantize(METRIC_SCALE, rounding=ROUND_HALF_UP))


def _nearest_rank(values: list[int], quantile: float) -> int:
    if not values:
        raise ValueError("cannot calculate a quantile for an empty dataset")
    ordered = sorted(values)
    rank = max(1, math.ceil(quantile * len(ordered)))
    return ordered[rank - 1]


def calculate_baseline_metrics(
    instances: list[ProcessInstance],
    role_rates: dict[str, Decimal],
    sla_minutes: int,
) -> dict[str, Any]:
    if not instances:
        raise ValueError("at least one process instance is required")

    cycles: list[int] = []
    touches: list[int] = []
    waits: list[int] = []
    labor_costs: list[Decimal] = []
    handoffs: list[int] = []
    step_wait_total: dict[str, int] = defaultdict(int)
    step_touch_total: dict[str, int] = defaultdict(int)
    role_touch_total: dict[str, int] = defaultdict(int)
    control_pass = 0
    control_applicable = 0

    for instance in instances:
        touch = sum(event.service_minutes for event in instance.events)
        wait = sum(event.wait_minutes for event in instance.events)
        cycles.append(touch + wait)
        touches.append(touch)
        waits.append(wait)
        labor_costs.append(
            sum(
                Decimal(event.service_minutes) * role_rates[event.role_id] / Decimal(60)
                for event in instance.events
            )
        )
        handoffs.append(
            sum(
                current.role_id != previous.role_id
                for previous, current in zip(instance.events, instance.events[1:])
            )
        )
        for event in instance.events:
            step_wait_total[event.step_id] += event.wait_minutes
            step_touch_total[event.step_id] += event.service_minutes
            role_touch_total[event.role_id] += event.service_minutes
        for status in instance.control_results.values():
            control_applicable += 1
            control_pass += status == "PASS"

    count = len(instances)
    total_cycle = sum(cycles)
    total_wait = sum(waits)
    exception_count = sum(bool(item.exception_reasons) for item in instances)
    audit_pass = sum(item.control_results["C-05"] == "PASS" for item in instances)
    high_risk = [item for item in instances if item.risk_tier == "HIGH"]
    high_risk_approved = sum(item.control_results.get("C-03") == "PASS" for item in high_risk)
    exception_items = [item for item in instances if item.exception_reasons]
    exception_controlled = sum(item.control_results.get("C-04") == "PASS" for item in exception_items)

    step_wait = {
        step_id: _rounded(Decimal(minutes) / Decimal(count))
        for step_id, minutes in sorted(step_wait_total.items())
    }
    step_touch = {
        step_id: _rounded(Decimal(minutes) / Decimal(count))
        for step_id, minutes in sorted(step_touch_total.items())
    }
    role_hours = {
        role_id: _rounded(Decimal(minutes) / Decimal(60))
        for role_id, minutes in sorted(role_touch_total.items())
    }
    bottleneck_order = [
        step_id
        for step_id, _ in sorted(
            step_wait.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    return {
        "dataset": {
            "instance_count": count,
            "business_days": len({item.received_day for item in instances}),
            "average_daily_volume": _rounded(Decimal(count) / Decimal(30)),
        },
        "time": {
            "average_cycle_minutes": _rounded(statistics.mean(cycles)),
            "median_cycle_minutes": _rounded(statistics.median(cycles)),
            "p90_cycle_minutes": _nearest_rank(cycles, 0.90),
            "minimum_cycle_minutes": min(cycles),
            "maximum_cycle_minutes": max(cycles),
            "average_touch_minutes": _rounded(statistics.mean(touches)),
            "average_wait_minutes": _rounded(statistics.mean(waits)),
            "wait_share_of_cycle": _rounded(Decimal(total_wait) / Decimal(total_cycle)),
            "sla_minutes": sla_minutes,
            "sla_attainment_rate": _rounded(
                Decimal(sum(value <= sla_minutes for value in cycles)) / Decimal(count)
            ),
        },
        "quality_and_flow": {
            "first_pass_yield": _rounded(Decimal(count - exception_count) / Decimal(count)),
            "exception_rate": _rounded(Decimal(exception_count) / Decimal(count)),
            "average_handoffs": _rounded(statistics.mean(handoffs)),
            "duplicate_rekey_touch_minutes_per_case": step_touch["crm_rekey"],
        },
        "cost_and_capacity": {
            "average_labor_cost_usd": _rounded(sum(labor_costs) / Decimal(count)),
            "role_workload_hours": role_hours,
        },
        "controls": {
            "applicable_control_completion_rate": _rounded(
                Decimal(control_pass) / Decimal(control_applicable)
            ),
            "activation_audit_evidence_rate": _rounded(Decimal(audit_pass) / Decimal(count)),
            "high_risk_manual_approval_rate": _rounded(
                Decimal(high_risk_approved) / Decimal(len(high_risk))
            ),
            "exception_path_control_rate": _rounded(
                Decimal(exception_controlled) / Decimal(len(exception_items))
            ),
        },
        "diagnostics": {
            "average_wait_minutes_by_step": step_wait,
            "average_touch_minutes_by_step": step_touch,
            "bottleneck_order_by_average_wait": bottleneck_order,
        },
    }


def load_role_rates(role_source: dict[str, Any]) -> dict[str, Decimal]:
    return {
        str(role["role_id"]): decimal_rate(role["synthetic_hourly_cost_usd"])
        for role in role_source["roles"]
    }
