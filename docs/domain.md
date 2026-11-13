# Domain

> The shared language between business, humans, and agents. Filled at bootstrap (2026-11-07),
> revised at bootstrap (2026-11-14): Leave Manager for the production workforce of one vehicle
> assembly plant of **ThrottleMaster**, a fictional car maker. Office/HQ staff, dealers, payroll
> and shift scheduling are out of scope.
> If a term isn't here, expect the AI to invent its own meaning for it.

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Employee | A production worker at the plant who requests leave. Belongs to exactly one Line and has exactly one Manager (none for the top of the tree). | Not "user" in domain code; "user" is only the logged-in identity in `http/`. |
| Manager | An Employee who approves or rejects the Leave requests of their direct reports. | Called "line supervisor" on the shop floor — same thing; the domain and code say Manager. Only *direct* reports — no skip-level approval. |
| Line | A production line (e.g. Body, Paint, Final Assembly). Has one Manager; its Employees are that Manager's direct reports. | Not a shift. The Manager is not counted in the Line's headcount. |
| Minimum staffing | The fewest Employees of a Line who must be at work on a Working day. A number per Line. | Reference data (BR-8), not derived. |
| Plant shutdown | A fixed date range when the whole plant is closed (e.g. summer shutdown, Christmas break). | Set by HR as reference data (BR-8); never requested, never a Leave request. |
| Leave request | A request by an Employee for a date range off (start date … end date, inclusive). | Not an "absence" — a request may never be taken (Rejected, Cancelled). |
| Leave type | `Annual` (counts against the Leave balance) or `Unpaid` (does not). | No other types in v1. |
| Leave balance | Annual days left for the Employee in the current calendar year. | Derived, never stored as an editable number. |
| Working day | Monday–Friday, excluding Plant shutdown days. No public-holiday calendar in v1. | A request's length is counted in Working days, not calendar days. |
| Status | `Pending` → `Approved` / `Rejected` (by the Manager) or `Cancelled` (by the requester). | Approved, Rejected, Cancelled are final. |

Not in v1: **Shift** (Early/Late/Night) — rotating shifts need a roster; that is its own product.

## Business rules
- **BR-1:** A Leave request's end date is on or after its start date; its length is the number of Working days in the range (inclusive), and must be ≥ 1. A request entirely inside a Plant shutdown is therefore refused. The start date is not before today (spec 0002).
- **BR-2:** An `Annual` request cannot exceed the Leave balance; `Pending` Annual requests count as already reserved.
- **BR-3:** An Employee cannot have two overlapping Leave requests that are `Pending` or `Approved`.
- **BR-4:** Only the requester's own Manager may approve or reject a request; nobody approves or rejects their own.
- **BR-5:** A request in `Approved`, `Rejected` or `Cancelled` is immutable. Only the requester may cancel, and only while `Pending`.
- **BR-6:** Every Employee starts each calendar year with 20 Annual days. No carry-over. A request spanning two years is refused in v1. Plant shutdown days are not Working days, so they never use Annual days.
- **BR-7:** A Manager cannot approve a request if, on any Working day in its range, the Line's Employees at work would fall below the Line's Minimum staffing. At work = the Line's Employees (Manager excluded) − those with `Approved` leave that day − this request's requester. Requesting stays allowed; only approval is blocked, and the refusal names the first short-staffed day.
- **BR-8:** Lines, Minimum staffing and Plant shutdowns are reference data, seeded in v1. No admin UI.

## Key domain invariants
- The Leave balance never goes below 0 (Approved + Pending Annual days ≤ 20 per year).
- A Status transition only ever moves out of `Pending`.
- On every Working day, a Line's at-work count is ≥ its Minimum staffing, as far as approvals can cause it (BR-7).

## Sensitive areas
- **Authorization** — who may approve/reject whose requests (BR-4), the Minimum staffing check
  on approval (BR-7), and who may see whose data: an Employee sees only their own requests, a
  Manager their own Line's requests and staffing, never another Line's (`docs/security.md`,
  AuthN / AuthZ). A spec touching any of it states `Sensitive area: Authorization`.
