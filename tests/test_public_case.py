from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.redesign import build_comparison


class PublicCaseTests(unittest.TestCase):
    def test_readme_states_human_authority(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("human", text.lower())
        self.assertIn("advisory", text.lower())

    def test_readme_contains_all_three_options(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for option in ("OPT-A", "OPT-B", "OPT-C"):
            self.assertIn(option, text)

    def test_public_demo_html_has_no_selection(self) -> None:
        text = (ROOT / "docs" / "assets" / "default-comparison.html").read_text(encoding="utf-8")
        self.assertIn("No human selection yet", text)

    def test_public_claims_remain_synthetic(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("synthetic", text)
        self.assertIn("not a production forecast", text)

    def test_default_candidate_remains_balanced(self) -> None:
        self.assertEqual(build_comparison(ROOT)["top_scoring_candidate"], "OPT-B")


if __name__ == "__main__":
    unittest.main()
