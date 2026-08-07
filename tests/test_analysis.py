from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from process_redesign_agent.analysis import analysis_digest, build_as_is_analysis, validate_analysis


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = build_as_is_analysis(ROOT)

    def test_analysis_is_valid(self) -> None:
        validate_analysis(self.analysis)

    def test_exception_resolution_is_highest_wait(self) -> None:
        self.assertEqual(self.analysis["step_diagnostics"][0]["step_id"], "exception_resolution")

    def test_all_five_controls_are_traced(self) -> None:
        ids = {item["control_id"] for item in self.analysis["mandatory_control_traceability"]}
        self.assertEqual(ids, {"C-01", "C-02", "C-03", "C-04", "C-05"})

    def test_answer_key_is_not_a_runtime_dependency(self) -> None:
        self.assertNotIn("answer-key", json.dumps(self.analysis, sort_keys=True))

    def test_bottlenecks_have_evidence(self) -> None:
        self.assertTrue(all(item["evidence_refs"] for item in self.analysis["bottlenecks"]))

    def test_ownership_problem_is_explicit(self) -> None:
        steps = {item["step_id"] for item in self.analysis["ownership_findings"]}
        self.assertIn("intake_receive", steps)
        self.assertIn("exception_resolution", steps)

    def test_digest_is_deterministic(self) -> None:
        self.assertEqual(analysis_digest(self.analysis), analysis_digest(build_as_is_analysis(ROOT)))


if __name__ == "__main__":
    unittest.main()
