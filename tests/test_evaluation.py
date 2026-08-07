from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.evaluation import evaluate_repository, validate_evaluation
from process_redesign_agent.redesign import build_comparison


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = evaluate_repository(ROOT)

    def test_evaluation_passes(self) -> None:
        validate_evaluation(self.result)
        self.assertTrue(self.result["all_checks_pass"])

    def test_default_ranking_starts_with_balanced(self) -> None:
        self.assertEqual(self.result["default_ranking"][0], "OPT-B")

    def test_claim_boundary_rejects_forecast_claim(self) -> None:
        self.assertIn("does not establish production forecast accuracy", self.result["claim_boundary"])

    def test_runtime_source_does_not_reference_answer_key(self) -> None:
        self.assertTrue(self.result["checks"]["runtime_does_not_reference_answer_key"])

    def test_every_projection_has_assumption_notice(self) -> None:
        comparison = build_comparison(ROOT)
        for projection in comparison["projections"]:
            self.assertIn("not a production forecast", projection["assumption_notice"])

    def test_all_controls_gate_before_ranking(self) -> None:
        comparison = build_comparison(ROOT)
        self.assertTrue(all(item["hard_controls_pass"] for item in comparison["projections"]))

    def test_evaluation_json_contains_no_private_data_marker(self) -> None:
        self.assertNotIn("CONFIDENTIAL", json.dumps(self.result))


if __name__ == "__main__":
    unittest.main()
