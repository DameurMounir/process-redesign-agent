from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.decision import create_comparison_run, export_run, select_option, show_run


class DecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        shutil.copytree(ROOT / "case", self.repo / "case")
        shutil.copytree(ROOT / "design", self.repo / "design")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_run_starts_without_a_decision(self) -> None:
        run = create_comparison_run(self.repo, "RUN-001")
        self.assertEqual(run["status"], "AWAITING_HUMAN_SELECTION")
        self.assertIsNone(run["decision"])

    def test_human_can_select_non_top_option(self) -> None:
        run = create_comparison_run(self.repo, "RUN-002")
        selected = select_option(self.repo, "RUN-002", "OPT-A", "reviewer-1", run["comparison_digest"], "Prefer the lower-change pilot for this review.")
        self.assertEqual(selected["decision"]["option_id"], "OPT-A")
        self.assertEqual(selected["decision"]["authority"], "HUMAN")

    def test_stale_digest_is_rejected(self) -> None:
        create_comparison_run(self.repo, "RUN-003")
        with self.assertRaises(ValueError):
            select_option(self.repo, "RUN-003", "OPT-B", "reviewer-1", "0" * 64, "This should fail because the digest is stale.")

    def test_path_traversal_run_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            create_comparison_run(self.repo, "../escape")

    def test_invalid_option_is_rejected(self) -> None:
        run = create_comparison_run(self.repo, "RUN-004")
        with self.assertRaises(ValueError):
            select_option(self.repo, "RUN-004", "OPT-X", "reviewer-1", run["comparison_digest"], "Unknown options cannot be selected here.")

    def test_selection_is_one_way(self) -> None:
        run = create_comparison_run(self.repo, "RUN-005")
        select_option(self.repo, "RUN-005", "OPT-B", "reviewer-1", run["comparison_digest"], "Balanced option is selected for this synthetic case.")
        with self.assertRaises(ValueError):
            select_option(self.repo, "RUN-005", "OPT-A", "reviewer-1", run["comparison_digest"], "Trying to overwrite a completed selection is blocked.")

    def test_export_requires_selection(self) -> None:
        create_comparison_run(self.repo, "RUN-006")
        with self.assertRaises(ValueError):
            export_run(self.repo, "RUN-006")

    def test_selected_run_exports_three_formats(self) -> None:
        run = create_comparison_run(self.repo, "RUN-007")
        select_option(self.repo, "RUN-007", "OPT-B", "reviewer-1", run["comparison_digest"], "Balanced option has the best accepted trade-off for the case.")
        output = export_run(self.repo, "RUN-007")
        self.assertTrue((output / "decision.json").exists())
        self.assertTrue((output / "decision.md").exists())
        self.assertTrue((output / "decision.html").exists())
        self.assertEqual(show_run(self.repo, "RUN-007")["status"], "HUMAN_SELECTED")
        self.assertEqual(json.loads((output / "decision.json").read_text())["run_id"], "RUN-007")


if __name__ == "__main__":
    unittest.main()
