# Fork maintenance

The upstream project is `javaht/claude-desktop-zh-cn`. Keep `main` as a fast-forward-only upstream mirror. Make and test compatibility changes on `katou/windows-compat`; bring new upstream code into this branch through a reviewable PR. Do not force-push either branch.

Read `maintenance/README.zh-CN.md` and `maintenance/compatibility.json` before an installation or adaptation. Prefer an equivalent upstream fix when it becomes available. Unknown or ambiguous bundle anchors require investigation, not guessed substitutions. The locale helper must remain idempotent and preserve explicit non-English locale overrides.

Scheduled tracking checks may fetch upstream, inspect installed-version/localization status and create or update an upstream-review PR in this Fork. They do not close Claude or install patches. When the user requests installation, back up the current version, verify ASAR/executable integrity and JavaScript syntax, then observe the restarted UI before claiming success. Preserve CC Switch configuration.

Never commit original application binaries, ASARs, user configurations, CC Switch databases, credentials, chat history or raw local logs. Store machine-specific tracking state under ignored `.maintenance/`. Retain only sanitized evidence summaries in `maintenance/`.

Run the upstream Python regression suite and the PowerShell locale-preference tests for changes to installation behavior. The Windows PowerShell 5.1 path matters because the Windows launcher uses it. GitHub Actions sync must never force-update `main` or merge unreviewed upstream changes into the compatibility branch.
