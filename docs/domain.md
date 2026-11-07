# Domain

> The shared language between business, humans, and agents. Filled at bootstrap (2026-11-07).
> If a term isn't here, expect the AI to invent its own meaning for it.

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Employee | A person who requests leave. Has exactly one Manager (none for the top of the tree). | Not "user" in domain code; "user" is only the logged-in identity in `http/`. |
| Manager | An Employee who approves or rejects the Leave requests of their direct reports. | Only *direct* reports — no skip-level approval. |
| Leave request | A request by an Employee for a date range off (start date … end date, inclusive). | Not an "absence" — a request may never be taken (Rejected, Cancelled). |
| Leave type | `Annual` (counts against the Leave balance) or `Unpaid` (does not). | No other types in v1. |
| Leave balance | Annual days left for the Employee in the current calendar year. | Derived, never stored as an editable number. |
| Working day | Monday–Friday. No public-holiday calendar in v1. | A request's length is counted in working days, not calendar days. |
| Status | `Pending` → `Approved` / `Rejected` (by the Manager) or `Cancelled` (by the requester). | Approved, Rejected, Cancelled are final. |

## Business rules
- **BR-1:** A Leave request's end date is on or after its start date; its length is the number of Working days in the range (inclusive), and must be ≥ 1.
- **BR-2:** An `Annual` request cannot exceed the Leave balance; `Pending` Annual requests count as already reserved.
- **BR-3:** An Employee cannot have two overlapping Leave requests that are `Pending` or `Approved`.
- **BR-4:** Only the requester's own Manager may approve or reject a request; nobody approves or rejects their own.
- **BR-5:** A request in `Approved`, `Rejected` or `Cancelled` is immutable. Only the requester may cancel, and only while `Pending`.
- **BR-6:** Every Employee starts each calendar year with 20 Annual days. No carry-over. A request spanning two years is refused in v1.

## Key domain invariants
- The Leave balance never goes below 0 (Approved + Pending Annual days ≤ 20 per year).
- A Status transition only ever moves out of `Pending`.

## Sensitive areas
- **Authorization** — who may approve/reject whose requests (BR-4) and who may see whose data
  (`docs/security.md`, AuthN / AuthZ). A spec touching it states `Sensitive area: Authorization`.
