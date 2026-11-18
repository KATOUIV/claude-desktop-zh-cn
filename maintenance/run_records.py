"""Allowlisted maintenance metadata, with bounded retention of our own records only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ERROR_CODES = frozenset({"tracking_failed", "invalid_tracking_state", "github_command_failed",
                         "github_timeout", "github_permission_denied", "github_auth_failed",
                         "github_rate_limited", "github_not_found", "mirror_diverged", "report_write_failed"})
OWNED_NAME = re.compile(r"check-(\d{8}T\d{6}Z)-[0-9a-f]{32}\.json\Z")
RETENTION_DAYS = 30
MAX_RECORDS = 120


def utc_now():
    return datetime.now(timezone.utc)


def sanitize(payload, now=None):
    """Never copy arbitrary error text, paths, commands, environment or nested state."""
    now = (now or utc_now()).astimezone(timezone.utc)
    status = payload.get("status")
    record = {"schema_version": 1, "timestamp_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
              "status": status if status in {"current", "review_needed", "failed", "local_check"} else "failed"}
    code = payload.get("error_code")
    if record["status"] == "failed":
        record["error_code"] = code if code in ERROR_CODES else "tracking_failed"
    patterns = {"run_id": r"[0-9]{1,24}", "release": r"v?[0-9]+(?:\.[0-9]+){1,3}(?:-[a-zA-Z0-9.-]+)?",
                "claude_version": r"[0-9]+(?:\.[0-9]+){1,3}", "mirror_sha": r"[0-9a-f]{40}",
                "fork_sha": r"[0-9a-f]{40}",
                "release_url": r"https://github\.com/javaht/claude-desktop-zh-cn/releases/tag/v?[0-9]+(?:\.[0-9]+){1,3}(?:-[a-zA-Z0-9.-]+)?",
                "fork_release_url": r"https://github\.com/KATOUIV/claude-desktop-zh-cn/releases/tag/v?[0-9]+\.[0-9]+\.[0-9]+",
                "pull_request": r"https://github\.com/KATOUIV/claude-desktop-zh-cn/pull/[0-9]+"}
    for key, pattern in patterns.items():
        value = payload.get(key)
        if isinstance(value, str) and len(value) <= 180 and re.fullmatch(pattern, value):
            record[key] = value
    for key in ("pending_commits", "compatibility_only_commits"):
        value = payload.get(key)
        if type(value) is int and 0 <= value <= 1_000_000:
            record[key] = value
    # Retry time and run ID do not create a new incident fingerprint.
    identity = {k: v for k, v in record.items() if k not in {"timestamp_utc", "run_id"}}
    record["fingerprint"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    return record


def records_folder(root):
    root = Path(root).resolve(strict=True)
    folder = root / ".maintenance" / "records"
    # resolve also detects Windows junctions; no redirected directory is managed.
    if folder.resolve() != folder or (root / ".maintenance").is_symlink() or folder.is_symlink():
        raise ValueError("Redirected maintenance directory")
    return folder


def write_record(repository_root, payload, now=None):
    now = (now or utc_now()).astimezone(timezone.utc)
    folder = records_folder(repository_root)
    folder.mkdir(parents=True, exist_ok=True)
    name = "check-" + now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex + ".json"
    destination = folder / name
    temporary = folder / (name + ".tmp")
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as stream:
            stream.write(json.dumps(sanitize(payload, now=now), ensure_ascii=False, indent=2) + "\n")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    # Only our exact filename format, in this exact folder, is eligible for deletion.
    if records_folder(repository_root) != folder:
        raise ValueError("Maintenance directory changed")
    owned = []
    for path in folder.iterdir():
        match = OWNED_NAME.fullmatch(path.name)
        if not match or path.is_symlink() or not path.is_file() or path.resolve().parent != folder:
            continue
        try:
            stamp = datetime.strptime(match[1], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if stamp < now - timedelta(days=RETENTION_DAYS):
            path.unlink()
        else:
            owned.append((stamp, path.name, path))
    for _, _, path in sorted(owned, reverse=True)[MAX_RECORDS:]:
        path.unlink()
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path(".maintenance/tracking-state.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        source = args.state if args.state.is_absolute() else root / args.state
        # This command reads only the known maintenance state, never arbitrary app files.
        if source.resolve() != root / ".maintenance" / "tracking-state.json" or source.is_symlink():
            raise ValueError("Unexpected state path")
        if source.stat().st_size > 1_048_576:
            raise ValueError("Oversized state")
        state = json.loads(source.read_text(encoding="utf-8-sig"))
        payload = {"status": state.get("maintenanceCheckStatus", "local_check"),
                   "error_code": state.get("maintenanceCheckErrorCode"), "release": state.get("upstreamRelease"),
                   "mirror_sha": state.get("upstreamCommit"), "fork_sha": state.get("forkCommit"),
                   "claude_version": state.get("claudeVersion"), "pending_commits": state.get("pendingUpstreamCommits")}
        write_record(root, payload)
    except Exception:
        print("Maintenance record failed: invalid state or record storage unavailable.", file=sys.stderr)
        raise SystemExit(1) from None
    print("Sanitized maintenance record saved; retention enforced (30 days, at most 120 records).")


if __name__ == "__main__":
    main()
