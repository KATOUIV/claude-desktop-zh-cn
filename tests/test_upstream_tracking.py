"""Remote GitHub responses are simulated; no installed applications are accessed."""
import importlib.util
import contextlib
import io
import json
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "maintenance" / "track_upstream.py"


class FakeGitHub:
    def __init__(self, pending=2, pulls=None, fail_sync=False):
        self.pending = pending
        self.pulls = pulls or []
        for pr in self.pulls:
            pr.setdefault("head", {"ref": "main", "repo": {"full_name": "KATOUIV/claude-desktop-zh-cn"}})
        self.fail_sync = fail_sync
        self.calls = []
        self.next_page = False

    def sync(self):
        self.calls.append(("sync",))
        if self.fail_sync:
            raise RuntimeError("mirror diverged")

    def api(self, endpoint, method="GET", data=None):
        self.calls.append((method, endpoint, data))
        if endpoint.endswith("releases/latest"):
            return {"tag_name": "1.4.24", "html_url": "https://github.com/javaht/claude-desktop-zh-cn/releases/tag/1.4.24"}
        if endpoint.endswith("/git/ref/heads/main"):
            return {"object": {"sha": "a" * 40}}
        if "/compare/" in endpoint:
            return {"ahead_by": self.pending, "behind_by": 3, "files": [{"filename": "scripts/install_windows.ps1"}]}
        if "/pulls?" in endpoint:
            if "page=2" in endpoint:
                return self.pulls
            if self.next_page:
                return [{} for _ in range(100)]
            return self.pulls
        if method == "POST" and endpoint.endswith("/pulls"):
            pr = {"number": 3, "body": data["body"], "html_url": "https://github.com/KATOUIV/claude-desktop-zh-cn/pull/3", "head": {"ref": "main", "repo": {"full_name": "KATOUIV/claude-desktop-zh-cn"}}}
            self.pulls = [pr]
            return pr
        if method == "PATCH":
            self.pulls[0].update(data)
            return self.pulls[0]
        raise AssertionError((endpoint, method, data))


class UpstreamTrackingTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "tracking coordinator must exist")
        spec = importlib.util.spec_from_file_location("upstream_tracker", SCRIPT)
        self.tracker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tracker)

    def test_no_pending_commits_does_not_create_pr(self):
        client = FakeGitHub(pending=0)
        result = self.tracker.track(client)
        self.assertEqual(result["pending_commits"], 0)
        self.assertFalse(any(c[0] in ("POST", "PATCH") for c in client.calls))

    def test_new_changes_create_only_a_draft_from_main(self):
        client = FakeGitHub()
        result = self.tracker.track(client)
        create = [c for c in client.calls if c[0] == "POST"]
        self.assertEqual(len(create), 1)
        self.assertTrue(create[0][2]["draft"])
        self.assertEqual(create[0][2]["head"], "main")
        self.assertEqual(create[0][2]["base"], "katou/windows-compat")
        self.assertIn("1.4.24", create[0][2]["body"])
        self.assertIn("scripts/install_windows.ps1", create[0][2]["body"])
        self.assertIn("pull/3", result["pull_request"])

    def test_repeated_identical_run_does_not_edit_or_duplicate_pr(self):
        client = FakeGitHub()
        self.tracker.track(client)
        client.calls.clear()
        self.tracker.track(client)
        self.assertFalse(any(c[0] in ("POST", "PATCH") for c in client.calls))

    def test_existing_human_review_is_preserved_when_tracking_changes(self):
        client = FakeGitHub(pulls=[{"number": 7, "body": "保留审阅结论：需要检查服务控制。", "html_url": "https://github.com/KATOUIV/claude-desktop-zh-cn/pull/7"}])
        self.tracker.track(client)
        client.pending = 4
        self.tracker.track(client)
        body = client.pulls[0]["body"]
        self.assertTrue(body.startswith("保留审阅结论：需要检查服务控制。"))
        self.assertEqual(body.count(self.tracker.BEGIN), 1)
        self.assertIn("4", body)
        self.assertFalse(any(c[0] == "POST" for c in client.calls))

    def test_existing_pull_request_on_second_page_is_reused(self):
        client = FakeGitHub(pulls=[{"number": 7, "body": "Review", "html_url": "https://github.com/KATOUIV/claude-desktop-zh-cn/pull/7"}])
        client.next_page = True
        self.tracker.track(client)
        self.assertFalse(any(c[0] == "POST" for c in client.calls))

    def test_failed_mirror_sync_stops_before_other_operations(self):
        client = FakeGitHub(fail_sync=True)
        with self.assertRaisesRegex(RuntimeError, "diverged"):
            self.tracker.track(client)
        self.assertEqual(client.calls, [("sync",)])

    def test_foreign_repository_is_rejected_before_any_calls(self):
        client = FakeGitHub()
        with self.assertRaises(ValueError):
            self.tracker.track(client, repository="javaht/claude-desktop-zh-cn")
        self.assertEqual(client.calls, [])

    def test_duplicate_tracking_blocks_are_not_silently_overwritten(self):
        body = self.tracker.BEGIN + "x" + self.tracker.END + self.tracker.BEGIN + "y" + self.tracker.END
        client = FakeGitHub(pulls=[{"number": 7, "body": body, "html_url": "url"}])
        with self.assertRaises(ValueError):
            self.tracker.track(client)
        self.assertFalse(any(c[0] in ("POST", "PATCH") for c in client.calls))

    def test_cli_success_writes_real_metadata_and_summary_files(self):
        with tempfile.TemporaryDirectory() as temp:
            report, summary = Path(temp) / "report.json", Path(temp) / "summary.md"
            arguments = [str(SCRIPT), "--repository", self.tracker.REPOSITORY,
                         "--report", str(report), "--summary", str(summary)]
            with patch("sys.argv", arguments), patch.object(self.tracker, "GitHub", return_value=FakeGitHub(pending=0)), contextlib.redirect_stdout(io.StringIO()):
                self.tracker.main()
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "current")
            self.assertIn('"pending_commits": 0', summary.read_text(encoding="utf-8"))

    def test_cli_failure_writes_report_and_still_fails_the_job(self):
        client = FakeGitHub(fail_sync=True)
        with tempfile.TemporaryDirectory() as temp:
            report, summary = Path(temp) / "report.json", Path(temp) / "summary.md"
            arguments = [str(SCRIPT), "--repository", self.tracker.REPOSITORY,
                         "--report", str(report), "--summary", str(summary)]
            with patch("sys.argv", arguments), patch.object(self.tracker, "GitHub", return_value=client), contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as failure:
                    self.tracker.main()
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(failure.exception.code, 1)
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_code"], "tracking_failed")
            self.assertNotIn("mirror diverged", report.read_text() + summary.read_text() + stderr.getvalue())
            self.assertEqual(client.calls, [("sync",)])

    def test_subprocess_error_never_contains_raw_diagnostics(self):
        response = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr="HTTP 403 FAKE_PRIVATE_TEXT")
        with patch.object(self.tracker.subprocess, "run", return_value=response):
            with self.assertRaises(self.tracker.TrackingError) as error:
                self.tracker.GitHub.run(["gh", "api"])
        self.assertEqual(error.exception.code, "github_permission_denied")
        self.assertNotIn("FAKE_PRIVATE_TEXT", str(error.exception))

    def test_subprocess_timeout_has_safe_code(self):
        with patch.object(self.tracker.subprocess, "run", side_effect=subprocess.TimeoutExpired("FAKE_PRIVATE_TEXT", 90)):
            with self.assertRaises(self.tracker.TrackingError) as error:
                self.tracker.GitHub.run(["gh", "api"])
        self.assertEqual(str(error.exception), "github_timeout")


if __name__ == "__main__":
    unittest.main()
