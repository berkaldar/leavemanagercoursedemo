# Architecture

> Filled at bootstrap (2026-11-07), revised 2026-11-14 (ThrottleMaster plant domain). The architecture decided on, not an aspiration.

## System overview
Leave Manager for the ThrottleMaster assembly plant (fictional car maker) is a **modular monolith**: one Python 3.14 process (FastAPI) serves a JSON API under
`/api` and the static frontend (plain HTML/CSS/ES modules, no build step) from `web/`. Data lives
in a single SQLite database through the stdlib `sqlite3`. Backend code is split into packages with
enforced boundaries so business rules stay pure and testable. Reason: one developer, one team's
data, a course demo — services would add operations cost and teach nothing about the rules (ADR 0001).

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `app/leave/` | Leave requests, Working-day counting, balance math, Status machine, Plant shutdowns in Working-day counting, the Minimum staffing check on approval (BR-1..BR-8) and its authorization decisions | Leave requests, Plant shutdowns |
| `app/people/` | Employees, the Manager relation, Lines and their Minimum staffing, the seeded people | Employees, Lines |
| `app/http/` | FastAPI routers, session, Pydantic boundary models: validate input → call a module's public API → map the result to HTTP | Live session ids, in process memory (not persistent) |
| `app/result.py` | `Ok` / `Err` / `ErrorCode` shared by the domain packages (`docs/conventions.md`, Error handling) | — |
| `app/db/` | Opening SQLite connections, migrations, seed (people, Lines, Minimum staffing, Plant shutdowns — BR-8) | The connection and schema |
| `app/main.py` | `create_app()`: wires routers, middleware, static files | — |
| `web/` | Static UI (`index.html`, `css/`, `js/`); talks to the API over HTTP only | Nothing persistent |

## Communication rules
- Packages call each other directly, only through the other package's `__init__.py` (its public API).
- No events, queues or background jobs in v1.
- `web/` reaches the server only via `fetch` to `/api/...`; no server-rendered templates.
- "Today" is passed in (an injected `Clock`, a FastAPI dependency), never read inside `app/leave/`.

## Forbidden dependencies (make them testable)
Asserted by `tests/test_architecture.py`, which reads imports with the stdlib `ast` module.
1. `app.leave` and `app.people` never import `app.http`.
2. Only `app.http` and `app.main` import `fastapi` or `starlette`.
3. `app.leave` uses `app.people` only through `app.people` itself, never its internal modules.
4. Only `app.db` imports `sqlite3`.
5. `app.leave` never calls `date.today()`, `datetime.now()` or `datetime.utcnow()`.

## Deliberately out of scope
Email or other notifications · public holidays · half days · carry-over between years ·
multiple plants/tenants · shift rosters · an admin UI for people, Lines, Minimum staffing or Plant shutdowns (all seeded) · real login with passwords ·
a frontend framework or build step · deployment with real people's data.
