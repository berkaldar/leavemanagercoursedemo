# Backlog — deferred findings

Findings a human triaged as **defer**: real, but fixed later by decision (`workflows/feature-development.md`,
step 7). Nothing lands here without that decision; noise is rejected in the triage record, not parked here.

- A criterion moved out at the ship gate (R-08, `→ moved to B-<n>`) lands here too, by the
  human's ship decision; the entry names the spec and criterion.
- One entry per finding, newest last. Delete the entry in the commit of the work that closes it.
- An entry that grows into new behavior becomes a spec (`specs/active/`), not a fix.

<!-- Format (labels stay English):
- **B-<n>** — <finding, one line> — Source: spec <NNNN>, review round <n> (<file:line>) — Severity: <…>
  — Recommendation: <the reviewer's action> — Deferred by: <name>, <YYYY-MM-DD>, <why>
  A decision deferred at bootstrap (its REPORT) uses Source: bootstrap <YYYY-MM-DD>.
-->

- **B-1** — UI error states outside spec 0001: a `/me` 500 or network error shows the login screen as if logged out; a refused login is swallowed silently; a failed logout is an unhandled rejection; a failed `/people` leaves a blank page — Source: spec 0001, review round 1 (`web/js/app.js:21,50-51,65,70`) — Severity: Info — Recommendation: give login/logout/people failures an error state in the next UI spec — Deferred by: Berk, 2026-11-07, no criterion affected; belongs with the next UI spec
- **B-2** — Starlette deprecates `httpx` in its test client in favour of `httpx2` (warning in every test run) — Source: spec 0001, build (`.venv/.../fastapi/testclient.py:1`) — Severity: Info — Recommendation: swap the pinned `httpx` for `httpx2` in `requirements-dev.txt` in a chore — Deferred by: Berk, 2026-11-07, a warning only; dependency change outside this spec
