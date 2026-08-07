from __future__ import annotations

import hashlib
import html
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from process_redesign_agent.redesign import DEFAULT_WEIGHTS, build_comparison, comparison_digest, validate_comparison

RUN_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,63}$")
REVIEWER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@+-]{1,127}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_root(repo: Path) -> Path:
    return repo / ".process-redesign"


def _safe_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must be 3-64 safe uppercase identifier characters")
    return run_id


def _run_path(repo: Path, run_id: str) -> Path:
    return _state_root(repo) / "runs" / f"{_safe_run_id(run_id)}.json"


def _load_run(repo: Path, run_id: str) -> dict[str, Any]:
    path = _run_path(repo, run_id)
    if not path.exists():
        raise FileNotFoundError(f"run does not exist: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def create_comparison_run(repo: Path, run_id: str, weights: dict[str, float] | None = None) -> dict[str, Any]:
    run_id = _safe_run_id(run_id)
    path = _run_path(repo, run_id)
    if path.exists():
        raise FileExistsError(f"run already exists: {run_id}")
    comparison = build_comparison(repo, DEFAULT_WEIGHTS if weights is None else weights)
    validate_comparison(comparison)
    digest = comparison_digest(comparison)
    value = {
        "run_id": run_id,
        "status": "AWAITING_HUMAN_SELECTION",
        "comparison_digest": digest,
        "comparison": comparison,
        "created_at_utc": _utc_now(),
        "decision": None,
    }
    _write_atomic(path, value)
    return value


def select_option(
    repo: Path,
    run_id: str,
    option_id: str,
    reviewer_id: str,
    expected_digest: str,
    rationale: str,
) -> dict[str, Any]:
    if not REVIEWER_RE.fullmatch(reviewer_id):
        raise ValueError("reviewer_id contains unsupported characters")
    if len(rationale.strip()) < 10:
        raise ValueError("selection rationale must contain at least 10 characters")
    run = _load_run(repo, run_id)
    if run["status"] != "AWAITING_HUMAN_SELECTION":
        raise ValueError("run is no longer awaiting a human selection")
    current = build_comparison(repo, {key: float(value) for key, value in run["comparison"]["weights"].items()})
    current_digest = comparison_digest(current)
    if current_digest != run["comparison_digest"] or current_digest != expected_digest:
        raise ValueError("stale or changed comparison digest; create a fresh review round")
    projection = next((item for item in current["projections"] if item["option_id"] == option_id), None)
    if projection is None:
        raise ValueError("selected option is not in the comparison")
    if not projection["hard_controls_pass"]:
        raise ValueError("an option that violates a mandatory control cannot be selected")
    run["status"] = "HUMAN_SELECTED"
    run["decision"] = {
        "option_id": option_id,
        "reviewer_id": reviewer_id,
        "rationale": rationale.strip(),
        "comparison_digest": current_digest,
        "decision_nonce": secrets.token_hex(16),
        "selected_at_utc": _utc_now(),
        "authority": "HUMAN",
    }
    _write_atomic(_run_path(repo, run_id), run)
    return run


def show_run(repo: Path, run_id: str) -> dict[str, Any]:
    return _load_run(repo, run_id)


def _markdown(run: dict[str, Any]) -> str:
    lines = [
        f"# Process redesign decision — {run['run_id']}",
        "",
        f"Status: **{run['status']}**",
        "",
        "| Option | Score | Avg cycle min | P90 min | SLA | FPY | Pilot envelope |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in run["comparison"]["projections"]:
        p = item["projected"]
        lines.append(
            f"| {item['option_id']} — {item['name']} | {item['tradeoff_score']:.4f} | {p['average_cycle_minutes']:.1f} | {p['p90_cycle_minutes']:.1f} | {p['sla_attainment_rate']:.1%} | {p['first_pass_yield']:.1%} | {'PASS' if item['soft_12_week_180k_constraint_pass'] else 'EXCEEDS'} |"
        )
    lines += ["", f"Top-scoring candidate: **{run['comparison']['top_scoring_candidate']}** (advisory only).", ""]
    if run["decision"]:
        decision = run["decision"]
        lines += [
            f"Human-selected option: **{decision['option_id']}**",
            f"Reviewer: `{decision['reviewer_id']}`",
            f"Rationale: {decision['rationale']}",
            f"Bound comparison digest: `{decision['comparison_digest']}`",
            "",
        ]
    lines.append("All projections are synthetic scenario transformations, not realized savings or production forecasts.")
    return "\n".join(lines) + "\n"


def _html(run: dict[str, Any]) -> str:
    rows = []
    for item in run["comparison"]["projections"]:
        p = item["projected"]
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['option_id'])}</td><td>{html.escape(item['name'])}</td>"
            f"<td>{item['tradeoff_score']:.4f}</td><td>{p['average_cycle_minutes']:.1f}</td>"
            f"<td>{p['p90_cycle_minutes']:.1f}</td><td>{p['sla_attainment_rate']:.1%}</td>"
            f"<td>{p['first_pass_yield']:.1%}</td><td>{'PASS' if item['soft_12_week_180k_constraint_pass'] else 'EXCEEDS'}</td>"
            "</tr>"
        )
    decision = run.get("decision")
    decision_html = (
        f"<p><strong>Human selected:</strong> {html.escape(decision['option_id'])} — {html.escape(decision['rationale'])}</p>"
        if decision
        else "<p><strong>No human selection yet.</strong></p>"
    )
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Process redesign decision {html.escape(run['run_id'])}</title><style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#172033}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5e1;padding:10px;text-align:left}}th{{background:#f3f6fa}}.note{{background:#fff7ed;padding:14px;border-left:4px solid #f59e0b}}</style></head><body><h1>Process redesign decision</h1><p>Run <code>{html.escape(run['run_id'])}</code> · status <strong>{html.escape(run['status'])}</strong></p><table><thead><tr><th>Option</th><th>Name</th><th>Score</th><th>Avg cycle</th><th>P90</th><th>SLA</th><th>FPY</th><th>Pilot envelope</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p>Top-scoring candidate: <strong>{html.escape(run['comparison']['top_scoring_candidate'])}</strong> (advisory only).</p>{decision_html}<div class=\"note\">Synthetic deterministic scenario comparison; not a production forecast or realized benefit claim.</div></body></html>"""


def export_run(repo: Path, run_id: str) -> Path:
    run = _load_run(repo, run_id)
    if run["status"] != "HUMAN_SELECTED":
        raise ValueError("export requires an explicit human selection")
    output = repo / "outputs" / _safe_run_id(run_id)
    output.mkdir(parents=True, exist_ok=True)
    (output / "decision.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "decision.md").write_text(_markdown(run), encoding="utf-8")
    (output / "decision.html").write_text(_html(run), encoding="utf-8")
    return output


def render_html_for_run(run: dict[str, Any]) -> str:
    return _html(run)
