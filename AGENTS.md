# AGENTS.md

Guidance for AI coding agents working in this repository. Human docs live in `README.md`.

## What this is

A stateless FastAPI app (no database) that fetches BMKG earthquake/tsunami feeds,
normalises them, and serves (a) a JSON API under `/api/v1` and (b) server-rendered
HTML shells whose data loads client-side from that API. Deployed on Vercel.

## Commands

```bash
uv sync                                   # install (creates .venv)
uv run uvicorn app.main:app --reload      # dev server → http://localhost:8000
uv run pytest                             # tests; upstream is mocked with respx
uv run ruff check . && uv run ruff format --check .
```

Always run tests and Ruff before finishing a change. Add dependencies with `uv add`
(or `uv add --dev`), never by hand-editing versions without re-locking.

## Layout

```
app/
  main.py            create_app(): lifespan (httpx client), error handlers, routers, /static mount
  schemas.py         Public API contract (Pydantic). Change deliberately — it's what clients consume.
  core/config.py     Settings from env (.env locally). BMKG_API is a SecretStr.
  core/cache.py      In-process TTL cache with stale-on-error
  core/security.py   Security headers + CSP (pure ASGI middleware)
  bmkg/client.py     Async upstream client: feed names, TTLs, media kinds, narrative sanitising
  bmkg/parsers.py    Pure functions: raw BMKG payload → schemas (no I/O; unit-test here)
  api/v1/routes.py   JSON endpoints
  web/pages.py       Page registry → routes, nav, SEO, sitemap
  web/routes.py      HTML pages, robots.txt, sitemap.xml, manifest
  templates/         Jinja2: base.html, layouts/, partials/, pages/
  static/css/app.css The whole design system (tokens → base → components)
  static/js/         ES modules: app.js (global), lib/*, pages/<page>.js
  static/vendor/     Leaflet 1.9.4 (vendored; SRI-verified)
tests/               pytest; fixtures/ holds trimmed real upstream payloads
```

## Hard rules

1. **Never expose the upstream URL.** `BMKG_API` must not appear in HTML, JSON, logs,
   error messages, or client JS. Images and narratives go through `/api/v1/media/...`
   and `/api/v1/earthquakes/{id}/narrative`. `UpstreamError` messages are generic.
   `tests/test_api.py::test_secret_never_leaks` guards this — keep it passing.
2. **Never commit `.env`** or real secrets. Document new settings in `.env.example`.
3. **No CSS frameworks, no jQuery, no build step.** Styling is `app/static/css/app.css`
   using the tokens in `:root`. Don't hard-code colours in components; add a token.
4. **Build DOM with `h()` from `static/js/lib/dom.js`** (text nodes only). The single
   `innerHTML` use is the narrative, which is sanitised server-side with `nh3`.
5. **Validate path params** (regex/enums) before they reach upstream URLs.
6. Keep `parsers.py` pure. Anything that needs the network belongs in `client.py`.

## Conventions

- Python 3.13, type hints everywhere, Ruff (line length 100).
- API responses: English snake_case keys, numbers as numbers, ISO 8601 datetimes with
  offsets, lists wrapped in `Envelope` (`data` + `meta`). Set `Cache-Control` per route.
- UI copy is **Indonesian**. Times are displayed in **WIB** via `lib/format.js`.
- Magnitude colour comes only from `magBucket()` / `--m-*` tokens (same scale everywhere).
- Static URLs in templates are plain paths with `?v={{ asset_version }}` — don't use
  `url_for` (it builds absolute URLs that break behind proxies).

## Adding things

- **New page:** add a `Page` to `app/web/pages.py`, a template in `templates/pages/`,
  and (if interactive) `static/js/pages/<name>.js`. Routes, nav, and sitemap follow.
- **New feed/endpoint:** add the file to `Feed` + TTL in `bmkg/client.py`, a parser in
  `parsers.py`, a schema in `schemas.py`, a route in `api/v1/routes.py`, a trimmed fixture
  in `tests/fixtures/`, and tests.

## Upstream data notes

- Realtime (`live30event.xml`), archives and history are **UTC**; alert feeds (latest,
  felt, M5+, tsunami) are **WIB** with `dd-mm-yy` dates. Parsers normalise both.
- Alert coordinates come as `lon,lat` in `<point>`; text fields use `LS/LU/BT/BB`.
- Tsunami feed is a flat list of bulletins (PD-1…PD-4); `parse_tsunami` groups them
  per earthquake by origin time/location proximity.
- Narratives exist mostly for M5+ events; upstream returns 403 when missing → our 404.

## Deployment

Vercel detects `app` in `app/main.py`. `pyproject.toml` sets
`[tool.vercel.fastapi.static] cdn = true` so `/static` is served from the CDN.
`vercel.json` holds function limits and static cache headers.
