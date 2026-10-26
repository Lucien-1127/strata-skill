"""Regression suite for the sellable Agent Evidence Closeout Gate skill."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent-evidence-closeout-gate" / "scripts"))
from verify_closeout import validate, load_report, DuplicateKeyError

DIMS = ("functional", "safety", "regression", "customer")


class ReliabilityAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        checks = []
        for dimension in DIMS:
            filename = dimension + ".txt"
            payload = ("Observed " + dimension + " check passed\n").encode()
            (self.root / filename).write_bytes(payload)
            checks.append({
                "id": dimension + "-01",
                "dimension": dimension,
                "result": "pass",
                "executed": True,
                "exit_code": 0,
                "evidence_path": filename,
                "evidence_sha256": hashlib.sha256(payload).hexdigest(),
            })
        self.report = {
            "schema_version": "1.0",
            "task_id": "example-1",
            "objective": "Verify four evidence-backed gates",
            "status": "completed",
            "attempts": 1,
            "max_attempts": 3,
            "blockers": [],
            "checks": checks,
        }

    def verdict(self):
        return validate(self.report, self.root)["verdict"]

    def test_four_evidence_gates_pass(self):
        outcome = validate(self.report, self.root)
        self.assertEqual(outcome["verdict"], "evidence_consistent")
        self.assertEqual(outcome["exit_code"], 0)
        self.assertEqual(set(outcome["checked_gates"]), set(DIMS))

    def test_missing_customer_gate_blocks_completion(self):
        self.report["checks"].pop()
        self.assertEqual(self.verdict(), "invalid")

    def test_failed_gate_blocks_completion(self):
        self.report["checks"][1]["result"] = "fail"
        self.assertEqual(self.verdict(), "invalid")

    def test_unexecuted_pass_is_invalid(self):
        self.report["checks"][0]["executed"] = False
        self.assertEqual(self.verdict(), "invalid")

    def test_hash_mismatch_is_invalid(self):
        (self.root / "safety.txt").write_text("changed after the run")
        self.assertEqual(self.verdict(), "invalid")

    def test_missing_evidence_is_invalid(self):
        (self.root / "safety.txt").unlink()
        self.assertEqual(self.verdict(), "invalid")

    def test_empty_evidence_is_invalid(self):
        (self.root / "customer.txt").write_bytes(b"")
        self.assertEqual(self.verdict(), "invalid")

    def test_traversal_is_invalid(self):
        self.report["checks"][0]["evidence_path"] = "../outside.txt"
        self.assertEqual(self.verdict(), "invalid")

    def test_symlink_is_invalid(self):
        (self.root / "functional.txt").unlink()
        (self.root / "functional.txt").symlink_to(self.root / "safety.txt")
        self.assertEqual(self.verdict(), "invalid")

    def test_duplicate_check_id_is_invalid(self):
        self.report["checks"][1]["id"] = self.report["checks"][0]["id"]
        self.assertEqual(self.verdict(), "invalid")

    def test_exceeded_retry_limit_is_invalid(self):
        self.report["attempts"] = 4
        self.assertEqual(self.verdict(), "invalid")

    def test_completed_with_blocker_is_invalid(self):
        self.report["blockers"] = ["Missing permission"]
        self.assertEqual(self.verdict(), "invalid")

    def test_blocked_is_honest_unresolved(self):
        self.report.update(status="blocked", attempts=0, blockers=["No repository permission"], checks=[])
        out = validate(self.report, self.root)
        self.assertEqual(out["verdict"], "unresolved")
        self.assertEqual(out["exit_code"], 2)

    def test_blocked_without_reason_is_invalid(self):
        self.report.update(status="blocked", attempts=0, blockers=[], checks=[])
        self.assertEqual(self.verdict(), "invalid")

    def test_regression_can_be_unresolved(self):
        self.report.update(status="regressed")
        self.report["checks"][2]["result"] = "fail"
        self.assertEqual(self.verdict(), "unresolved")

    def test_unhashable_status_is_invalid_without_crash(self):
        self.report["status"] = ["completed"]
        self.assertEqual(self.verdict(), "invalid")

    def test_unhashable_dimension_is_invalid_without_crash(self):
        self.report["checks"][0]["dimension"] = ["functional"]
        self.assertEqual(self.verdict(), "invalid")

    def _run_cli(self):
        import subprocess
        report_path = self.root / "report.json"
        report_path.write_text(json.dumps(self.report), encoding="utf-8")
        script = ROOT / "agent-evidence-closeout-gate" / "scripts" / "verify_closeout.py"
        result = subprocess.run(
            [sys.executable, str(script), "--report", str(report_path),
             "--evidence-root", str(self.root)],
            text=True, capture_output=True, check=False, timeout=10
        )
        return result.returncode, json.loads(result.stdout)

    def test_cli_completed_returns_zero(self):
        code, output = self._run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(output["verdict"], "evidence_consistent")

    def test_cli_blocked_returns_two(self):
        self.report.update(status="blocked", attempts=0, checks=[],
                           blockers=["Approval for deployment missing"])
        code, output = self._run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(output["verdict"], "unresolved")

    def test_cli_tampered_evidence_returns_one(self):
        (self.root / "safety.txt").write_text("Tampered evidence")
        code, output = self._run_cli()
        self.assertEqual(code, 1)
        self.assertEqual(output["verdict"], "invalid")

    def test_regressed_without_failed_executed_check_is_invalid(self):
        self.report["status"] = "regressed"
        self.assertEqual(self.verdict(), "invalid")

    def test_regressed_without_actual_execution_is_invalid(self):
        self.report["status"] = "regressed"
        self.report["checks"][2]["result"] = "fail"
        self.report["checks"][2]["executed"] = False
        self.report["checks"][2]["exit_code"] = None
        self.assertEqual(self.verdict(), "invalid")

    def test_no_progress_without_retry_is_invalid(self):
        self.report["status"] = "no_progress"
        self.report["attempts"] = 1
        self.assertEqual(self.verdict(), "invalid")

    def test_no_progress_after_two_failed_attempts_is_unresolved(self):
        self.report["status"] = "no_progress"
        self.report["attempts"] = 2
        self.report["checks"][0]["result"] = "fail"
        self.assertEqual(self.verdict(), "unresolved")

    def test_no_progress_with_all_checks_passing_is_invalid(self):
        self.report["status"] = "no_progress"
        self.report["attempts"] = 2
        self.assertEqual(self.verdict(), "invalid")

    def test_duplicate_json_keys_rejected(self):
        path = self.root / "duplicate.json"
        path.write_text('{"schema_version":"1.0","schema_version":"1.0"}')
        with self.assertRaises(DuplicateKeyError):
            load_report(path)

    def test_nonfinite_json_rejected(self):
        path = self.root / "nan.json"
        path.write_text('{"objective": NaN}')
        with self.assertRaises(ValueError):
            load_report(path)


if __name__ == "__main__":
    unittest.main()
