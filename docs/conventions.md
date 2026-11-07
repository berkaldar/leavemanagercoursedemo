# Conventions

> Filled at bootstrap (2026-11-07). Only rules that are real: every rule here is either enforced
> by tooling (preferred) or checked in review. Aspirations don't belong here.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): English
- Document language (docs/, specs, plans, ADRs, review and verify reports): English
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: English
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
Python 3.14 · FastAPI 0.162 · Uvicorn 0.54 (local run only) · itsdangerous 2.2 · pytest 9.2 ·
pytest-playwright (Chromium) · httpx 0.28 · ruff 0.17 · mypy 2.4 · pip-audit · stdlib `sqlite3`.
Frontend: plain HTML/CSS/ES modules, no npm, no build step.
Every dependency is pinned with `==` in `requirements.txt` (runtime) / `requirements-dev.txt` (dev,
includes `-r requirements.txt`); installed into `.venv` with pip. The Python version is pinned in
`.python-version`. Every check step calls the venv's Python through `scripts/py`.

**Setup & run:** `<python 3.14> -m venv .venv` (on Windows the full path, e.g.
`%LOCALAPPDATA%Pythonpythoncore-3.14-64python.exe`, if `python` is not on PATH) ·
`scripts/py -m pip install -r requirements-dev.txt` · `scripts/py -m playwright install chromium` ·
run locally: `scripts/py -m uvicorn --factory app.main:create_app_from_env` (database `LEAVE_DB`,
default `file:leave.db`).

## Naming
- Python: PEP 8 — `snake_case` modules, functions, variables; `PascalCase` classes; `UPPER_CASE` constants.
- Each package exposes its public API from `__init__.py`; everything else in the package is internal.
- Tests in `tests/`, mirroring `app/` (`tests/leave/test_rules.py`); e2e journeys in `tests/e2e/`,
  marked `e2e` (`docs/testing.md`).
- JS files `kebab-case.js`; functions and variables `camelCase` inside.
- Domain terms are spelled as in `docs/domain.md` (`LeaveRequest`, `LeaveType.ANNUAL`, `Status.PENDING`, …).

## Error handling
- Domain functions (`app.leave`, `app.people`) return frozen dataclasses `Ok[T] | Err`, where
  `Err.code` is an `ErrorCode` `StrEnum` (`INSUFFICIENT_BALANCE`, `OVERLAP`, `NOT_FOUND`,
  `NOT_PENDING`, …). They never raise for an expected rule violation.
- `app.http` maps each code to a status — invalid input 422 (FastAPI's validation default), not
  found *or out of your scope* 404, rule conflict 409 — with body `{"error": "<CODE>", "message": "<text>"}`.
- Anything unexpected → one exception handler → 500 `{"error": "INTERNAL"}`. Tracebacks, SQL and
  other people's data never reach the client.

## Data rules
- Leave dates are `datetime.date` in domain code (no time zone involved); stored in SQLite as ISO
  `TEXT`, sent in JSON as `YYYY-MM-DD`.
- Audit timestamps (`created_at`, `decided_at`) are timezone-aware UTC `datetime`, stored as ISO-8601 `TEXT`.
- Leave days are whole numbers of Working days (`int`).
- IDs are `str(uuid4())`.
- "Today" comes from an injected `Clock` (a FastAPI dependency); nothing in `app.leave` reads the system clock.
- Pydantic models live only in `app.http` (boundary, `extra="forbid"`); domain code uses dataclasses.

## Known traps
<!-- Starts empty. One line per trap of this stack that a builder can know up front:
     "<trap> — <what to do instead> — from <spec/finding>". A line is added when triage marks a
     finding real and the reviewer says a build-time rule would have caught it; the human
     approves it at triage as Amendment A-n and the Developer writes it in the fix round.
     Builders read this section before the first plan step.
     A trap that tooling can catch moves to "Enforced by tooling" instead. -->
- `sqlite3` does not enforce foreign keys by default — run `PRAGMA foreign_keys = ON` on every connection, in `app.db` — from bootstrap
- `sqlite3`'s built-in date adapters are deprecated (3.12+) — convert explicitly with `isoformat()` / `date.fromisoformat()`, never `detect_types` — from bootstrap
- `:memory:` is per connection and sync FastAPI endpoints run in a threadpool — one connection per request (a dependency with `yield`); tests use a named shared-cache memory DB (`file:<name>?mode=memory&cache=shared`, `uri=True`, `check_same_thread=False`) — from bootstrap
- `datetime.utcnow()` is naive and deprecated — `datetime.now(UTC)`, and only inside the `Clock` — from bootstrap
- Starlette's `Exception` handler runs in `ServerErrorMiddleware`, outside `@app.middleware` — headers a middleware sets are missing on 500s; set them in the handler too — from 0001 review (A-3)
- JS `innerHTML` with data is an XSS hole (vanilla JS has no auto-escaping) — build DOM with `createElement` / `textContent`; never put data into `innerHTML` — from bootstrap

## Enforced by tooling
<!-- Wire new rules into `scripts/check` whenever possible — prose is advice, tooling is law. -->
- mypy `--strict` (types step).
- ruff lint + `ruff format --check` (lint step), incl. `DTZ` (naive datetimes) and `S608` (string-built SQL).
- Forbidden dependencies 1–5 (`docs/architecture.md`) — `tests/test_architecture.py`.
- Not enforced by tooling here: the JS `innerHTML` rule — backed by the CSP header and review.
(Active once the walking skeleton adds the steps to `scripts/check.conf`.)
