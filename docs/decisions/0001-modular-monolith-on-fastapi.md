# ADR 0001 — Modular monolith on Python 3.14 + FastAPI + sqlite3, vanilla frontend

- Status: Accepted
- Date: 2026-11-07

## Context
Leave Manager is a course demo: one developer, one team's fake data, rules that must be easy to
test. The owner chose Python + FastAPI, SQLite and a plain JS/HTML/CSS frontend. Python 3.14 is
installed on the development machine (its `python` PATH alias is broken; the venv is used instead).

## Decision
Build one FastAPI process with packages `app.leave`, `app.people`, `app.http`, `app.db` whose
boundaries are enforced by an architecture test; store data with the stdlib `sqlite3`; serve the
frontend as static ES modules with no build step. Prove UI states with Playwright (Python) e2e
journeys under a budget (`docs/testing.md`).

## Consequences
- Buys: one language and one toolchain (pip + venv) for server and tests; no ORM, no frontend
  build, very few dependencies to audit; a memory database per test.
- Costs: UI states are proven by browser tests (slower, full-only) rather than component tests;
  vanilla JS has no auto-escaping, so XSS safety rests on a rule (Known traps), a CSP header and
  review; a single process does not scale horizontally — irrelevant at this size.

## Alternatives considered
- TypeScript / Node 24 / React (the first bootstrap proposal) — replaced by the owner's stack choice.
- Pure-function JS views tested with `node --test` — no browser, but a second runtime in check; the
  owner chose Playwright e2e.
- `uv` instead of pip — real lockfile and faster, but one more tool to install for a demo.

## Revisit triggers
The e2e budget (3 journeys / 90 s) is exceeded; UI logic grows beyond what vanilla JS keeps simple;
more than one team/tenant; a real deployment.
