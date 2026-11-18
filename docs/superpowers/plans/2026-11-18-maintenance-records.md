# Maintenance records and schedule audit

User delegated implementation without routine clarification. Extend the existing maintenance pipeline, not the application installer.

1. Test then implement allowlisted metadata: UTC timestamp, workflow ID, bounded version/commit/status fields, fixed error codes and stable fingerprints. Never persist exception text, commands, environment variables or private paths.
2. Test then implement local per-check atomic JSON records in ignored `.maintenance/records`: 30-day/120-record bounds, cleaning only owned filenames, rejecting paths escaping the repository and preserving all existing backups and unrelated files.
3. Refactor the cloud CLI to publish sanitized failures without raw tracebacks, use bounded subprocess timeouts and keep its token scoped to the tracking step. Preserve failure exit status and branch protections.
4. Set repository log retention to 30 days; retain the existing 14-day tracking artifacts. Update the existing daily task with exact record command and schedule/protection/retention checks; no duplicate task or client installation.
5. Run local relevant/full suites, independent review, protected PR Windows/Linux CI and a deployed cloud smoke test. Record deployment evidence locally.

Known local Linux symlink-privilege test errors must remain explicit; do not alter system permissions. Retention changes do not retroactively claim to delete old logs, and no broad cleanup of `.maintenance` is allowed.

Execution evidence: allowlist/rotation and tracking tests passed locally; the first implementation run followed failing tests for absent record support and leaked exception text. Full local regression retained five existing WinError 1314 Linux ASAR errors; locale-preference PowerShell tests passed. Repository retention was read back as 30 days, the existing daily automation was updated without a duplicate, and branch protections remain active with no bypass. Independent whole-branch review found no important blockers. A Windows junction fixture was added to cover directory redirection without requiring symlink privilege. Final cloud CI and deployed tracking verification are recorded in the integration PR and ignored local state.
