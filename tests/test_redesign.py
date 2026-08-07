from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.advisor import RuleAdvisor
from process_redesign_agent.analysis import build_as_is_analysis
from process_redesign_agent.redesign import DEFAULT_WEIGHTS, build_comparison, comparison_digest, sensitivity_profiles, validate_comparison, validate_weights


class RedesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.comparison = build_comparison(ROOT)

    def test_default_comparison_is_valid(self) -> None:
        validate_comparison(self.comparison)

    def test_three_options_are_compared(self) -> None:
        self.assertEqual({item["option_id"] for item in self.comparison["projections"]}, {"OPT-A", "OPT-B", "OPT-C"})

    def test_all_options_preserve_mandatory_controls(self) -> None:
        self.assertTrue(all(item["hard_controls_pass"] for item in self.comparison["projections"]))

    def test_balanced_option_is_default_candidate(self) -> None:
        self.assertEqual(self.comparison["top_scoring_candidate"], "OPT-B")

    def test_balanced_option_meets_operational_targets(self) -> None:
        item = next(item for item in self.comparison["projections"] if item["option_id"] == "OPT-B")
        self.assertTrue(all(item["target_status"].values()))
        self.assertTrue(item["soft_12_week_180k_constraint_pass"])

    def test_automation_first_exposes_delivery_constraint(self) -> None:
        item = next(item for item in self.comparison["projections"] if item["option_id"] == "OPT-C")
        self.assertFalse(item["soft_12_week_180k_constraint_pass"])

    def test_invalid_weights_are_rejected(self) -> None:
        bad = dict(DEFAULT_WEIGHTS)
        bad["change_risk"] = 0.5
        with self.assertRaises(ValueError):
            validate_weights(bad)

    def test_comparison_digest_is_stable(self) -> None:
        self.assertEqual(comparison_digest(self.comparison), comparison_digest(build_comparison(ROOT)))

    def test_advisor_cannot_claim_authority(self) -> None:
        explanation = RuleAdvisor().explain(build_as_is_analysis(ROOT), self.comparison)
        self.assertEqual(explanation["authority"], "ADVISORY_ONLY")

    def test_sensitivity_has_explicit_profiles(self) -> None:
        self.assertEqual(set(sensitivity_profiles(ROOT)), {"balanced", "speed", "cost_and_change"})


if __name__ == "__main__":
    unittest.main()
