
from __future__ import annotations

import json
import unittest
from pathlib import Path

from process_redesign_agent.generator import INSTANCE_COUNT, build_instance_records, check_generated_case

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PRESENT = (REPO_ROOT / "case/manifest.json").is_file()


@unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
class GeneratorTests(unittest.TestCase):
    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(build_instance_records(), build_instance_records())

    def test_expected_volume_and_identifiers(self) -> None:
        records = build_instance_records()
        self.assertEqual(len(records), INSTANCE_COUNT)
        self.assertEqual(records[0]["instance_id"], "AB-ONB-0001")
        self.assertEqual(records[-1]["instance_id"], "AB-ONB-0240")
        self.assertEqual(records[0]["received_day"], 1)
        self.assertEqual(records[-1]["received_day"], 30)

    def test_committed_generated_artifacts_do_not_drift(self) -> None:
        self.assertEqual(check_generated_case(REPO_ROOT), [])

    def test_jsonl_is_canonical_and_complete(self) -> None:
        lines = (REPO_ROOT / "case/operations/process-instances.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), INSTANCE_COUNT)
        for line in lines:
            value = json.loads(line)
            self.assertEqual(line, json.dumps(value, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
