
from __future__ import annotations

import unittest
from pathlib import Path

from process_redesign_agent.io import load_instances, load_json
from process_redesign_agent.metrics import calculate_baseline_metrics, load_role_rates

REPO_ROOT = Path(__file__).resolve().parents[1]


class MetricTests(unittest.TestCase):
    def test_calculator_matches_frozen_answer_key(self) -> None:
        case_root = REPO_ROOT / "case"
        instances = load_instances(case_root / "operations/process-instances.jsonl")
        roles = load_json(case_root / "sources/roles-and-rates.json")
        constraints = load_json(case_root / "sources/constraints-and-targets.json")
        expected = load_json(case_root / "expected/baseline-kpis.json")
        actual = calculate_baseline_metrics(
            instances,
            load_role_rates(roles),
            constraints["baseline"]["sla_working_minutes"],
        )
        self.assertEqual(actual, expected["metrics"])

    def test_baseline_exposes_material_tradeoff_drivers(self) -> None:
        metrics = load_json(REPO_ROOT / "case/expected/baseline-kpis.json")["metrics"]
        self.assertGreater(metrics["time"]["wait_share_of_cycle"], 0.80)
        self.assertLess(metrics["time"]["sla_attainment_rate"], 0.70)
        self.assertGreater(metrics["quality_and_flow"]["exception_rate"], 0.25)
        self.assertLess(metrics["controls"]["activation_audit_evidence_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
