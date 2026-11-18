# Fork maintenance

Follow upstream `javaht/claude-desktop-zh-cn`; keep only necessary Windows compatibility changes. `main` is a fast-forward-only mirror. Use protected PRs into `katou/windows-compat`; never force-push, discard local fixes or bypass required checks. Prefer equivalent upstream fixes.

Read `maintenance/README.zh-CN.md` and `maintenance/compatibility.json`. Keep locale handling idempotent, preserve explicit non-English overrides and the original Cowork service binary. Unknown or ambiguous anchors must fail safely.

Use the upstream official Release as the default download source. Cloud tracking reads its metadata, fast-forwards main and maintains one draft PR; it never creates/edits Releases or tags. Existing Fork releases remain labeled backups. Preserve human notes outside the PR tracking block. The authorized daily check may review upstream changes, resolve confirmed conflicts in an integration branch and merge through a protected PR after required Windows/Linux checks pass. Review new code, dependencies and workflow permissions before executing tests; prefer GitHub-hosted CI. Never equate a draft PR with passing CI.

Maintenance never stops/restarts Claude, installs patches or changes client update settings. A separately requested installation requires backups, integrity/syntax checks and observed UI verification before updating the verified baseline.

Keep machine state, installed versions, local paths and detailed evidence only in ignored `.maintenance/`; do not publish them in files or PRs. Never access or upload credentials, private application configuration/databases, chat history or raw application logs. Use the existing GitHub token and hosted runners; synchronization needs no persistent personal token, local runner, inbound service or tunnel.

The README is the maintenance policy reference. Update `.maintenance/tracking-state.json`, then run `python maintenance/run_records.py --state .maintenance/tracking-state.json`. Keep only allowlisted metadata; never bulk-clean backups or unrelated files. Reuse the existing automation, check workflow/protection/retention health, and leave intentionally disabled Pages alone.

Run the upstream regression suite for executable changes. Installation changes also require PowerShell locale-preference tests, including Windows PowerShell 5.1. Report platform limitations honestly; never change system permissions just to pass tests.
