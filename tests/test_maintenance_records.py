import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "maintenance" / "run_records.py"


class MaintenanceRecordTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "allowlisted record implementation is required")
        spec = importlib.util.spec_from_file_location("run_records", SCRIPT)
        self.records = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.records)
        self.now = datetime(2026, 11, 18, 4, 0, tzinfo=timezone.utc)

    def test_only_allowlisted_metadata_is_retained(self):
        payload = {"status": "failed", "error_code": "tracking_failed", "run_id": "12345", "error": "FAKE_PRIVATE_TEXT", "token": "FAKE_PRIVATE_TEXT", "path": r"C:\private\FAKE_PRIVATE_TEXT", "release": "1.4.24", "mirror_sha": "a" * 40}
        record = self.records.sanitize(payload, now=self.now)
        text = json.dumps(record)
        self.assertNotIn("FAKE_PRIVATE_TEXT", text)
        self.assertNotIn("error", record)
        self.assertEqual(record["error_code"], "tracking_failed")
        self.assertEqual(record["timestamp_utc"], "2026-11-18T04:00:00Z")
        self.assertEqual(record["run_id"], "12345")

    def test_fingerprint_is_stable_across_retries_but_changes_with_cause(self):
        a = self.records.sanitize({"status": "failed", "error_code": "tracking_failed", "run_id": "1"}, now=self.now)
        b = self.records.sanitize({"status": "failed", "error_code": "tracking_failed", "run_id": "2"}, now=self.now + timedelta(hours=6))
        c = self.records.sanitize({"status": "failed", "error_code": "github_timeout"}, now=self.now)
        self.assertEqual(a["fingerprint"], b["fingerprint"])
        self.assertNotEqual(a["fingerprint"], c["fingerprint"])

    def test_private_urls_and_invalid_fields_are_not_copied(self):
        result = self.records.sanitize({"status": "current", "run_id": "secret", "release_url": "https://other.example/private?token=FAKE_PRIVATE_TEXT", "claude_version": r"C:\private", "pending_commits": -1}, now=self.now)
        self.assertNotIn("run_id", result)
        self.assertNotIn("release_url", result)
        self.assertNotIn("claude_version", result)
        self.assertNotIn("pending_commits", result)

    def test_rotation_preserves_unowned_files_and_backups(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / ".maintenance" / "records"
            folder.mkdir(parents=True)
            backup = root / ".maintenance" / "before-reconcile.bundle"
            backup.write_text("keep backup")
            note = folder / "user-note.json"
            note.write_text("keep note")
            old = folder / ("check-" + (self.now - timedelta(days=31)).strftime("%Y%m%dT%H%M%SZ") + "-" + "a" * 32 + ".json")
            old.write_text("{}")
            for i in range(120):
                (folder / ("check-" + (self.now - timedelta(minutes=i + 1)).strftime("%Y%m%dT%H%M%SZ") + "-" + f"{i:032x}" + ".json")).write_text("{}")
            path = self.records.write_record(root, {"status": "local_check", "claude_version": "6.6395.0"}, now=self.now)
            self.assertFalse(old.exists())
            self.assertEqual(len(list(folder.glob("check-*.json"))), 120)
            self.assertEqual(json.loads(path.read_text())["claude_version"], "6.6395.0")
            self.assertTrue(backup.exists())
            self.assertTrue(note.exists())
            self.assertFalse(list(folder.glob("*.tmp")))

    def test_symlinked_record_folder_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / ".maintenance").mkdir()
            try:
                (root / ".maintenance" / "records").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("directory symlink privilege unavailable")
            with self.assertRaises(ValueError):
                self.records.write_record(root, {"status": "local_check"}, now=self.now)
            self.assertEqual(list(Path(outside).iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_windows_junction_cannot_redirect_record_rotation(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / ".maintenance").mkdir()
            folder = root / ".maintenance" / "records"
            sentinel = Path(outside) / "keep.json"
            sentinel.write_text("keep")
            environment = {**os.environ, "MAINT_RECORD_TEST_LINK": str(folder), "MAINT_RECORD_TEST_TARGET": outside}
            created = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                                      "New-Item -ItemType Junction -ErrorAction Stop -Path $env:MAINT_RECORD_TEST_LINK -Target $env:MAINT_RECORD_TEST_TARGET | Out-Null"],
                                     env=environment, capture_output=True, timeout=30)
            self.assertEqual(created.returncode, 0, "junction fixture creation failed")
            with self.assertRaises(ValueError):
                self.records.write_record(root, {"status": "local_check"}, now=self.now)
            self.assertEqual(sentinel.read_text(), "keep")
            self.assertEqual(len(list(Path(outside).iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
