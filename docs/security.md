# Security

> Filled at bootstrap (2026-11-07). Baseline rules agents must honor in every plan and review.

## Secrets
- Secrets never enter the repo, specs, prompts, or chat. `.env` is gitignored; provide `.env.example`.
- Agents never print secret values, even when debugging.
- The only secret in v1 is `SESSION_SECRET` (cookie signing), read from the environment; when unset,
  a random one is generated per process (sessions then end on restart). Tests pass a fixed one.

## Input & output
- Every route declares Pydantic models for body, params and query with `extra="forbid"`; dates are
  typed `date`, so malformed ones are rejected at the boundary (422).
- SQL only with `sqlite3` `?` placeholders — never string-built (ruff `S608`).
- Frontend: data enters the DOM only through `textContent` / `createElement`, never `innerHTML`
  (`docs/conventions.md`, Known traps). One middleware sets `Content-Security-Policy: default-src 'self'`
  on every response, so inline scripts never run.
- Error responses follow `docs/conventions.md` (Error handling): no tracebacks, SQL or other people's data.

## AuthN / AuthZ
- **AuthN (demo-grade, deliberate):** people are seeded; "login" = picking a seeded Employee. The
  session is Starlette `SessionMiddleware` — a signed (itsdangerous), `HttpOnly`, `SameSite=Lax`
  browser-session cookie that carries only a random session id; the server keeps the live ids and
  forgets one on logout and on any new login attempt, so a copied cookie does not outlive it. A new id on every login. No passwords. **This app is never deployed with real people's data.**
- **AuthZ — sensitive area (`docs/domain.md`), default-deny:** every `/api` route requires a session
  except login and the seeded-people list for the login screen. The decision is made in the
  `app.leave` / `app.people` domain functions, which take the acting Employee as an explicit
  parameter — never only in `app.http`, never in the frontend.
- An Employee sees and acts on their own requests; a Manager additionally sees and decides their
  direct reports' requests. Nobody decides their own request (BR-4).
- A resource outside the actor's scope answers **404**, not 403, so its existence does not leak.

## Dependencies
- A new runtime dependency is listed in the plan and approved by the human at the PLAN gate,
  with: license (MIT / Apache-2.0 / BSD / ISC / PSF only), maintained in the last 12 months, and
  why the standard library or an existing dependency is not enough.
- Runtime dependencies at bootstrap: `fastapi`, `uvicorn`, `itsdangerous`. Exact `==` pins.
- `pip-audit -r requirements.txt` runs in the full check profile.

## Review lens
Security is a mandatory dimension of every independent review (see `prompts/review.md`), not a
separate afterthought phase.
