from __future__ import annotations

import json
import unittest
from pathlib import Path

from process_redesign_agent.generator import INSTANCE_COUNT, build_instance_records, check_generated_case

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_PRESENT = (REPO_ROOT / "case/manifest.json").is_file()


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

    @unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
    def test_committed_generated_artifacts_do_not_drift(self) -> None:
        self.assertEqual(check_generated_case(REPO_ROOT), [])

    def test_volume_is_evenly_distributed_across_thirty_days(self) -> None:
        records = build_instance_records()
        counts = {day: 0 for day in range(1, 31)}
        for record in records:
            counts[record["received_day"]] += 1
        self.assertEqual(set(counts.values()), {8})

    def test_case_contains_no_preselected_future_option(self) -> None:
        records = build_instance_records()
        self.assertTrue(all("recommended_option" not in record for record in records))

    @unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
    def test_jsonl_is_canonical_and_complete(self) -> None:
        lines = (REPO_ROOT / "case/operations/process-instances.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), INSTANCE_COUNT)
        for line in lines:
            value = json.loads(line)
            self.assertEqual(line, json.dumps(value, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
