# Fork maintenance

The upstream project is `javaht/claude-desktop-zh-cn`. Keep `main` as a fast-forward-only upstream mirror. Make and test compatibility changes on `katou/windows-compat`; bring new upstream code into this branch through a reviewable PR. Do not force-push either branch.

Read `maintenance/README.zh-CN.md` and `maintenance/compatibility.json` before an installation or adaptation. Prefer an equivalent upstream fix when it becomes available. Unknown or ambiguous bundle anchors require investigation, not guessed substitutions. The locale helper must remain idempotent and preserve explicit non-English locale overrides.

Scheduled tracking checks may fetch upstream, inspect installed-version/localization status and create or update an upstream-review PR in this Fork. They do not close Claude or install patches. When the user requests installation, back up the current version, verify ASAR/executable integrity and JavaScript syntax, then observe the restarted UI before claiming success. Preserve CC Switch configuration.

The user delegated ongoing repository maintenance on 2026-11-18. Cloud tracking runs every six hours, fast-forwards main and maintains a draft main-to-compatibility PR; it never merges or executes upstream code. The daily Codex check may review the actual changes, prepare a separate integration branch when conflicts exist, run relevant tests and merge the reviewed PR only after required Windows/Linux checks pass under branch protection. Preserve local compatibility changes, retain merge ancestry and use no protection bypass. Unreviewed or failing changes stay pending. This authorization does not allow unattended installation, restarting Claude, changing its auto-update settings or accessing private application data.

The cloud PR body contains a machine-owned tracking block. Update only that block; preserve review notes elsewhere. Reuse an existing proposal, never create duplicate PRs. After integration, save the new branch/PR state in ignored .maintenance/tracking-state.json. Inspect track-upstream.yml health and the active branch rules; a stale/disabled workflow or missing protection must be investigated rather than silently bypassed.

Never commit original application binaries, ASARs, user configurations, CC Switch databases, credentials, chat history or raw local logs. Store machine-specific tracking state under ignored `.maintenance/`. Retain only sanitized evidence summaries in `maintenance/`.

Run the upstream Python regression suite and the PowerShell locale-preference tests for changes to installation behavior. The Windows PowerShell 5.1 path matters because the Windows launcher uses it. GitHub Actions sync must never force-update `main` or merge unreviewed upstream changes into the compatibility branch.
