
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from process_redesign_agent.generator import build_instance_records
from process_redesign_agent.models import ProcessInstance
from process_redesign_agent.validation import verify_repository_case

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PRESENT = (REPO_ROOT / "case/manifest.json").is_file()


class ValidationTests(unittest.TestCase):
    @unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
    def test_repository_case_contract_passes(self) -> None:
        summary = verify_repository_case(REPO_ROOT)
        self.assertEqual(summary["instance_count"], 240)
        self.assertEqual(summary["p90_cycle_minutes"], 1885)

    def test_event_sequence_tampering_is_rejected(self) -> None:
        record = copy.deepcopy(build_instance_records()[0])
        record["events"][1]["sequence"] = 99
        with self.assertRaisesRegex(ValueError, "sequence is not contiguous"):
            ProcessInstance.from_dict(record)

    def test_negative_minutes_are_rejected(self) -> None:
        record = copy.deepcopy(build_instance_records()[0])
        record["events"][0]["wait_minutes"] = -1
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            ProcessInstance.from_dict(record)


if __name__ == "__main__":
    unittest.main()
