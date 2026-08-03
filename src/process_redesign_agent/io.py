
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from process_redesign_agent.models import ProcessInstance


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def canonical_jsonl_bytes(values: Iterable[dict[str, Any]]) -> bytes:
    lines = [json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for item in values]
    return ("\n".join(lines) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_instances(path: Path) -> list[ProcessInstance]:
    instances: list[ProcessInstance] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL record must be an object at {path}:{line_number}")
            instances.append(ProcessInstance.from_dict(value))
    return instances


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
