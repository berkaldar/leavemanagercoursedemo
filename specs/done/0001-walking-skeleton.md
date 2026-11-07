# Spec 0001 — Walking skeleton: log in and see "My requests"

- Status: Shipped
- Mode: lite
- Plan: `specs/plans/0001-plan.md`
- Self-critique: done

## Intent
An Employee opens Leave Manager, picks themselves from the list of seeded people, and lands on a
"My requests" page that greets them by name and shows an empty list. Success is the whole path —
choosing who you are, staying recognised while you work, and being turned away when you are not
recognised — working end to end and proven by `scripts/check`, so every later feature builds on it.
Deliberately not done: creating, approving or cancelling requests, balances, and any Manager view.

## Requirements
- R-1: The system knows three seeded people: Deniz Kaya (Manager), and her direct reports Ali Demir
  and Elif Şahin (Employees).
- R-2: A person who is not logged in can choose one of the seeded people and log in as them,
  without a password (demo-grade, `docs/security.md`).
- R-3: Once logged in, the person stays logged in until they log out or close the browser; there
  is no timeout.
- R-4: A logged-in person sees the "My requests" page: their full name and the list of their own
  leave requests. In this spec nobody can have requests yet, so the list is always empty.
- R-5: A person who is not logged in cannot see "My requests" or learn who is logged in; they are
  sent to the login screen, and the system refuses such requests as "not logged in".
- R-6: Logging in as anyone other than a seeded person is refused and logs nobody in.
- R-7: A logged-in person can log out; afterwards they are no longer recognised.
- R-8: A logged-in person who opens the login screen is taken to "My requests".

## User experience
- Flow: open the app → login screen → choose your name in the "Who are you?" list → "Log in" →
  "My requests" page (heading "My requests", "Signed in as <full name>", "Log out" button) →
  "Log out" → login screen.
- States:
  - Login screen: the list shows the seeded people sorted alphabetically by full name
    (Ali Demir, Deniz Kaya, Elif Şahin); no one is preselected — "Log in" with no choice does nothing
    but ask for a choice ("Choose who you are.").
  - My requests — loading: "Loading your requests…" while the list is on its way.
  - My requests — empty: "You have no leave requests yet."
  - My requests — error: "Could not load your requests." with a "Try again" button; pressing it
    shows the loading state again and retries.
  - My requests — no permission (not logged in): the login screen is shown instead.
  - My requests — success (with rows): not reachable in this spec; it arrives with the spec that
    lets Employees create requests.
- Design reference: none — the flow above is the design.
- Accessibility: the whole flow works with the keyboard alone (Tab to the list, choose, Enter on
  "Log in"; Tab to "Log out"); the list has a visible label "Who are you?"; status messages
  (loading, empty, error) are announced to screen readers; text keeps WCAG AA contrast.

## Constraints & out of scope
- Sensitive area: Authorization (`docs/domain.md`) — this spec creates the session and the
  default-deny rule every later feature relies on.
- Walking skeleton: this spec creates the toolchain (`.venv`, `scripts/py`, requirements files,
  test configuration), activates every planned step in `scripts/check.conf` (with its `requires`
  lines), adds the architecture test and e2e journey J-1 (`docs/testing.md`), adds the Python and
  Playwright setup to CI, and runs the residue test on both profiles.
- Size: two small capabilities (log in/out, see "My requests") and 9 criteria — kept as one on
  purpose: a walking skeleton is by definition the smallest end-to-end slice; splitting it leaves
  either half untestable end to end.
- Out of scope: creating, approving, rejecting or cancelling requests; leave balances; any
  Manager-only view; passwords or real identity; session timeout; editing people; any visual
  styling beyond readable defaults.

## Acceptance criteria
- [x] AC-1 — The login screen lists exactly the three seeded people, alphabetically by full name: Ali Demir, Deniz Kaya, Elif Şahin (the "Ş" displays correctly), with none preselected.
- [x] AC-2 — Choosing a person and pressing "Log in" shows "My requests" with "Signed in as <that person's full name>"; pressing "Log in" with no choice shows "Choose who you are." and logs nobody in.
- [x] AC-3 — For a freshly seeded person, "My requests" shows "You have no leave requests yet."
- [x] AC-4 — While the list is loading, "Loading your requests…" is shown.
- [x] AC-5 — When the list cannot be loaded, "Could not load your requests." and a "Try again" button are shown; "Try again" shows the loading state and retries, and on success shows the empty state.
- [x] AC-6 — Without being logged in: opening "My requests" shows the login screen, and asking the system who is logged in or for "my requests" is refused as "not logged in", revealing no person's data.
- [x] AC-7 — Logging in as someone who is not a seeded person (e.g. an unknown or tampered identifier) is refused and logs nobody in.
- [x] AC-8 — After "Log out", the login screen is shown and the previous session is no longer recognised (AC-6 behavior applies to it); a logged-in person opening the login screen is taken to "My requests".
- [x] AC-9 — The flow log in → "My requests" → log out works with the keyboard alone; the people list has the visible label "Who are you?"; loading, empty and error messages are announced to screen readers.

## Verification
Criterion ↔ evidence (VERIFY, independent QA session, 2026-11-07). Full green: CHECK GREEN (full, 5 steps, 18 s) @a6470e2 — CI https://github.com/berkaldar/leavemanagercoursedemo/actions/runs/42373602910; later commits touch only `specs/`. Reproduce: `./scripts/check`.

| Acceptance criterion | Evidence | Status |
|---|---|---|
| AC-1 | `tests/people/test_people.py::test_list_people_sorted_by_full_name` · `tests/e2e/test_j1_login.py::test_login_screen_lists_seeded_people` · S-1 | PASS |
| AC-2 | `tests/http/test_session_api.py::test_login_then_me_returns_person` · `tests/e2e/test_j1_login.py::test_login_shows_name_and_requires_choice` · S-2, S-4 | PASS |
| AC-3 | `tests/leave/test_my_requests.py::test_only_own_requests_returned` · `tests/e2e/test_j1_login.py::test_my_requests_empty_state` · S-4 · broken on purpose: own-only filter removed → red | PASS |
| AC-4 | `tests/e2e/test_j1_login.py::test_my_requests_loading_state` · S-3 | PASS |
| AC-5 | `tests/e2e/test_j1_login.py::test_my_requests_error_then_retry` · S-5, S-6 | PASS |
| AC-6 | `tests/http/test_session_api.py::test_no_session_is_refused` · `tests/e2e/test_j1_login.py::test_no_session_shows_login` · S-7 · broken on purpose: missing session falls back to a person → red | PASS |
| AC-7 | `tests/http/test_session_api.py::test_login_unknown_person_refused` · `tests/http/test_session_api.py::test_refused_login_retires_the_previous_session` · broken on purpose: person check removed at login → red | PASS |
| AC-8 | `tests/http/test_session_api.py::test_logout_ends_session` · `tests/http/test_session_api.py::test_new_login_retires_the_previous_session` · `tests/e2e/test_j1_login.py::test_logout_and_logged_in_skips_login` · S-7 · broken on purpose: logout keeps the session id → red; login keeps the previous session id → red | PASS |
| AC-9 | `tests/e2e/test_j1_login.py::test_keyboard_only_flow_and_live_region` | PASS |

S-1…S-7 agent-captured, judged by Berk at SHIP, 2026-11-07 (login screen; "Choose who you are."; loading; empty; error with Try again; retry shows loading; logged out → login). Not in the repo (docs/testing.md, Evidence policy).

## Definition of Done
- [x] Every acceptance criterion mapped to proof (test or reproducible observation)
- [x] `scripts/check` green
- [x] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [x] Docs / ADRs updated if behavior or architecture changed
- [x] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | 0 |
| Fix rounds | 1 |
| Review findings: real / noise / deferred | 4 / 2 / 1 (+1 builder note deferred: B-2) |
| Regressions introduced | 0 |
| Bugs escaped to production | 0 (not deployed) |
