from __future__ import annotations

import copy
import shutil
import tempfile
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

    @unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
    def test_case_file_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(REPO_ROOT, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            target = copy_root / "case/sources/process-brief.md"
            target.write_text(target.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"manifest (?:byte count|digest) mismatch"):
                verify_repository_case(copy_root)

    @unittest.skipUnless(CASE_PRESENT, "Milestone 01 case not present")
    def test_manifest_covers_all_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(REPO_ROOT, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            (copy_root / "case/unmanifested.txt").write_text("unexpected\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest must cover"):
                verify_repository_case(copy_root)


if __name__ == "__main__":
    unittest.main()
