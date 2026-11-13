# Spec 0002 — Employee submits a leave request

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0002-plan.md`
- Self-critique: done

## Intent
A production Employee at the ThrottleMaster plant asks for time off from the "My requests" page
instead of on a paper form: they choose Annual or Unpaid leave and a date range, and the request
appears in their list as `Pending`, with its length in Working days. Success is that an Employee can
submit any valid request and is told plainly why an invalid one is refused — a reversed range, a
range with no Working days (weekends, Plant shutdowns), a past start date, a range across two
calendar years, or an overlap with a request they already have. Decided at clarify (2026-11-14,
Berk): this spec comes before F-1 (Leave balance), because a balance needs requests to count.
Deliberately not done: the Leave balance and its limit (F-1), approving, rejecting (F-2) and
cancelling (F-3).

## Requirements
- R-1: A logged-in Employee can submit a Leave request for themselves with a Leave type (`Annual`
  or `Unpaid`), a start date and an end date (inclusive). It is always the logged-in person's own
  request; nobody can submit one for someone else.
- R-2: A submitted request starts as `Pending` and shows in the requester's "My requests" list with
  its Leave type, start date, end date, length in Working days and Status, sorted by start date.
- R-3: The length is the number of Working days in the range: Monday–Friday, excluding Plant
  shutdown days (`docs/domain.md`).
- R-4: The plant has two seeded Plant shutdowns (invented, BR-8): Christmas break 2026-12-24 …
  2026-12-31 and summer shutdown 2027-07-26 … 2027-08-06.
- R-5: A request is refused, and nothing is saved, when:
  - the end date is before the start date (BR-1);
  - the range has no Working days, e.g. only a weekend or only Plant shutdown days (BR-1);
  - the start date is before today;
  - start and end fall in different calendar years (BR-6);
  - it overlaps, by at least one calendar day, another of the requester's requests that is
    `Pending` or `Approved` (BR-3) — requests of other Employees never block it;
  - the Leave type, start date or end date is missing or not valid.
- R-6: Each refusal tells the Employee the reason in one sentence; only the first failing reason
  is shown, in the order listed in R-5 (missing/invalid input is checked first).
- R-7: Someone who is not logged in cannot submit; the system refuses it as "not logged in".

## User experience
- Flow: "My requests" → "New request" form on the same page (Leave type, Start date, End date,
  "Submit request") → "Submit request" → success message, the form clears and the new row appears
  in the list as `Pending`.
- Form: "Leave type" is a choice of "Annual" and "Unpaid" with none preselected; "Start date" and
  "End date" are date fields; each has a visible label.
- States:
  - Submitting: "Submitting…" is shown and "Submit request" is disabled until the answer comes back.
  - Success: "Request submitted." is shown; the form is cleared; the list shows the new row.
  - Refused (a rule in R-5): the reason is shown next to the form and the entered values stay:
    - missing/invalid input: "Choose a leave type, a start date and an end date."
    - end before start: "The end date must be on or after the start date."
    - no Working days: "This range has no working days."
    - past start: "The start date cannot be in the past."
    - across two years: "A request must start and end in the same calendar year."
    - overlap: "You already have a pending or approved request on these dates."
  - Error (the request could not be sent or the system failed): "Could not submit your request.
    Try again." with the entered values kept; nothing is saved.
  - My requests — success (with rows): table with the columns Type, Start, End, Working days,
    Status; dates shown as YYYY-MM-DD. (Empty, loading and error states of the list are unchanged
    from spec 0001.)
  - No permission (not logged in): the login screen, as in spec 0001.
- Design reference: none — the flow above is the design.
- Accessibility: the whole form works with the keyboard alone (Tab through Leave type, Start date,
  End date, "Submit request"; Enter submits); every field has a visible label; the submitting,
  success, refused and error messages are announced to screen readers; text keeps WCAG AA contrast.

## Constraints & out of scope
- "Today" is the server's local date from the injected clock (`docs/architecture.md`), so tests
  fix it; the browser never decides it.
- The overlap check and the save happen as one step: of two simultaneous submissions that overlap
  (double submit, two tabs), the second is refused (R-5).
- Docs: the past-start rule is added to BR-1 in `docs/domain.md` in this spec's PR.
- Not a sensitive area: the owner of a request is always the logged-in person — there is no choice
  of whose request it is (AC-10). Authorization in `docs/domain.md` covers approval and visibility.
- e2e: this spec adds journey J-2 (`docs/testing.md`): submit a request that breaks a rule → the
  refused state is shown; it also submits a valid one → the row appears.
- Size: one capability (submit a request) with 11 criteria, slightly above the ~8–10 guide — kept
  as one: every criterion is a refusal reason or a state of the same form, and splitting the
  refusals away would ship a form that accepts invalid requests.
- Out of scope: Leave balance and BR-2 (F-1); approve/reject and BR-7 (F-2); cancel (F-3);
  editing or deleting a request; half days; public holidays; a reason/comment field; Lines and
  Minimum staffing (F-2); an admin UI for Plant shutdowns; an upper limit on length (Annual is
  capped by F-1; Unpaid has no cap in v1).

## Acceptance criteria
- [ ] AC-1 — A logged-in Employee submits Annual 2026-11-16 … 2026-11-20 (today = 2026-11-14): "Request submitted." is shown, the form clears, and "My requests" shows a row Annual · 2026-11-16 · 2026-11-20 · 5 · Pending; the same works for Unpaid.
- [ ] AC-2 — The Working-day count is Monday–Friday excluding Plant shutdown days: Fri 2026-11-20 … Mon 2026-11-23 counts 2; 2026-12-21 … 2026-12-31 counts 3 (only 21–23 Dec, the rest is the Christmas break); a single weekday counts 1.
- [ ] AC-3 — End date before start date is refused with "The end date must be on or after the start date."; end = start on a weekday is accepted.
- [ ] AC-4 — A range with no Working days is refused with "This range has no working days.": Sat 2026-11-21 … Sun 2026-11-22, and 2027-07-26 … 2027-08-06 (entirely the summer shutdown).
- [ ] AC-5 — A start date before today is refused with "The start date cannot be in the past."; a start date equal to today (a weekday) is accepted.
- [ ] AC-6 — A range from 2026-12-21 to 2027-01-04 is refused with "A request must start and end in the same calendar year."
- [ ] AC-7 — With a Pending (and, separately, an Approved) request 2026-11-16 … 2026-11-20, a new request sharing even one day (2026-11-20 … 2026-11-24) is refused with "You already have a pending or approved request on these dates."; one starting the day after (2026-11-23) is accepted; a Rejected or Cancelled request on the same days does not block; another Employee's request on the same days does not block.
- [ ] AC-8 — Missing Leave type, start date or end date, an unknown Leave type, or a malformed date is refused with "Choose a leave type, a start date and an end date."; when several rules fail, only the first reason in R-5 order is shown.
- [ ] AC-9 — Every refused or failed submission saves nothing (the list and stored requests are unchanged) and keeps the entered values in the form; a failed submission (system or network error) shows "Could not submit your request. Try again."; while waiting, "Submitting…" is shown and "Submit request" is disabled.
- [ ] AC-10 — The request is always stored for the logged-in person, whatever the submission says about who it is for; without being logged in, submitting is refused as "not logged in" and nothing is saved.
- [ ] AC-11 — The form works with the keyboard alone (Tab order Leave type → Start date → End date → "Submit request", Enter submits); each field has a visible label; the submitting, success, refused and error messages are announced to screen readers.

## Definition of Done
- [ ] Every acceptance criterion mapped to proof (test or reproducible observation)
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale, deferred ones in `specs/backlog.md`
- [ ] Docs / ADRs updated if behavior or architecture changed
- [ ] Spec moved to `specs/done/` (it becomes immutable there)

## Scorecard (fill at ship — honest numbers make the process improvable)
| Metric | Value |
|---|---|
| Spec revisions | |
| Fix rounds | |
| Review findings: real / noise / deferred | |
| Regressions introduced | |
| Bugs escaped to production | |
