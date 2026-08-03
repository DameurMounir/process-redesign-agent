from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class ProcessEvent:
    sequence: int
    step_id: str
    role_id: str
    service_minutes: int
    wait_minutes: int
    outcome: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ProcessEvent":
        event = cls(
            sequence=int(value["sequence"]),
            step_id=str(value["step_id"]),
            role_id=str(value["role_id"]),
            service_minutes=int(value["service_minutes"]),
            wait_minutes=int(value["wait_minutes"]),
            outcome=str(value["outcome"]),
        )
        if event.sequence < 1:
            raise ValueError("event sequence must be positive")
        if not event.step_id or not event.role_id:
            raise ValueError("event step_id and role_id are required")
        if event.service_minutes < 0 or event.wait_minutes < 0:
            raise ValueError("event minutes cannot be negative")
        return event


@dataclass(frozen=True, slots=True)
class ProcessInstance:
    case_version: str
    instance_id: str
    received_day: int
    risk_tier: str
    exception_reasons: tuple[str, ...]
    control_results: dict[str, str]
    events: tuple[ProcessEvent, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ProcessInstance":
        instance = cls(
            case_version=str(value["case_version"]),
            instance_id=str(value["instance_id"]),
            received_day=int(value["received_day"]),
            risk_tier=str(value["risk_tier"]),
            exception_reasons=tuple(str(item) for item in value["exception_reasons"]),
            control_results={str(k): str(v) for k, v in value["control_results"].items()},
            events=tuple(ProcessEvent.from_dict(item) for item in value["events"]),
        )
        if not instance.case_version:
            raise ValueError("case_version is required")
        if not instance.instance_id:
            raise ValueError("instance_id is required")
        if instance.received_day < 1:
            raise ValueError("received_day must be positive")
        if not instance.events:
            raise ValueError("at least one event is required")
        expected = list(range(1, len(instance.events) + 1))
        actual = [event.sequence for event in instance.events]
        if actual != expected:
            raise ValueError(f"event sequence is not contiguous for {instance.instance_id}")
        return instance


def decimal_rate(value: Any) -> Decimal:
    return Decimal(str(value))
