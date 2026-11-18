# Upstream tracking implementation plan

> Execute inline with test-first verification and a final independent review.

**Goal:** Keep the upstream mirror fresh without erasing Windows compatibility fixes or interrupting Claude.

**Architecture:** GitHub checks upstream every six hours, fast-forwards only main and creates/updates a single draft main-to-compatibility PR. The existing daily Codex heartbeat reviews, resolves conflicts and merges tested integration PRs under branch protection. Cloud tracking never merges compatibility changes or installs application patches.

**Tech stack:** GitHub Actions, gh CLI, Python standard library, existing Codex heartbeat.

**Constraints:** No force push, no branch-protection bypass, no unreviewed merge, no changes to running Claude or its user data. Use the existing automation rather than a second schedule. No new long-lived credentials. A GitHub-token-created draft does not imply CI ran; the agent must push a reviewed integration branch using its existing authenticated session to trigger full CI.

**Review focus:** Duplicate proposals; overwritten human review notes; failed mirror synchronization followed by writes; forbidden repositories; API pagination; temporary network/auth failures; stale workflows or disabled GitHub schedules.

- [ ] Add failing tests for the tracking coordinator, including unchanged runs, pagination, unsafe divergence failures and preserving review text.
- [ ] Implement the coordinator and six-hour workflow, report metadata as artifacts, use bounded job timeout and limited token permissions; test both success and failure reporting.
- [ ] Document cloud/agent responsibilities and update repository instructions to reflect the user's delegation. Update the existing heartbeat after deployment.
- [ ] Run local relevant tests and the full suite, document environment-limited Linux tests, run Windows/Linux cloud checks, obtain independent review and merge via protected PR.
- [ ] Enable only the GitHub setting needed for Actions to open its own draft PRs, verify a real workflow run, save local tracking state and report limits plainly.

User explicitly opted out of clarification and delegated implementation choices. Selected a six-hour cloud mirror plus daily agent review: it runs while the PC is off without unattended application installs or unreviewed compatibility merges.
