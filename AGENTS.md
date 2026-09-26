# AGENTS.md

Guidance for AI coding agents working in this repository. Human docs live in `README.md`;
the visual spec lives in `docs/design-brief.md`.

## What this is

A stateless FastAPI app (no database) that fetches BMKG earthquake/tsunami feeds,
normalises them, and serves:

- a JSON API under `/api/v1` (docs at `/docs`, `/redoc`);
- HTML pages that **server-render their primary content** (for SEO and first paint)
  and embed the same data as JSON; ES-module scripts hydrate from that JSON and keep it
  fresh from the API.

Deployed on Vercel (behind Cloudflare at gempa.rone.dev).

## Commands

```bash
uv sync                                   # install (creates .venv)
uv run uvicorn app.main:app --reload      # dev server → http://localhost:8000
uv run pytest                             # tests; upstream is mocked with respx
uv run ruff check . && uv run ruff format --check .
uv run --with pillow python scripts/make_og.py      # regenerate static/img/og.png
uv run --with pillow python scripts/make_icons.py   # regenerate favicons from the header mark
```

Always run tests and Ruff before finishing a change, and syntax-check edited JS with
`node --input-type=module --check < file.js`. Add dependencies with `uv add`
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
  web/routes.py      Page rendering: per-page data LOADERS, SEO (title, OG, JSON-LD), robots, sitemap
  web/format.py      Jinja filters mirroring static/js/lib/format.js (WIB, magnitude, depth…)
  web/icons.py       SVG icon set for templates: {{ icon("name") }} (mirrors static/js/lib/icons.js)
  templates/
    base.html        Head/SEO, header, footer, detail <dialog>, initial-data JSON
    layouts/map.html Adds Leaflet
    partials/        macros.html (mag_badge, event_item, realtime_row, facts, dial), page_head…
    pages/           One template per page
  static/css/app.css The whole design system (tokens → base → components → pages)
  static/js/         app.js (global), lib/* (api, dom, format, icons, map, ui, detail, initial), pages/*
  static/img/        favicon.svg/.ico/PNGs (generated, same mark as the header brand) + og.png
  static/vendor/     Leaflet 1.9.4 (vendored; SRI-verified)
docs/design-brief.md Design system spec ("Seismic Clay")
scripts/make_og.py   Generates the Open Graph image
scripts/make_icons.py Generates all favicons from the header seismograph mark
tests/               pytest; fixtures/ holds trimmed real upstream payloads
```

## Hard rules

1. **Never expose the upstream URL.** `BMKG_API` must not appear in HTML, JSON, logs,
   error messages, or client JS. Images and narratives go through `/api/v1/media/...`
   and `/api/v1/earthquakes/{id}/narrative`. `UpstreamError` messages are generic.
   `tests/test_api.py::test_secret_never_leaks` guards this — keep it passing.
2. **Never commit `.env`** or real secrets. Document new settings in `.env.example`.
3. **No CSS frameworks, no jQuery, no build step.** Styling is `app/static/css/app.css`.
4. **Build DOM with `h()` from `static/js/lib/dom.js`** (text nodes only). The single
   `innerHTML` use is the narrative, which is sanitised server-side with `nh3`.
5. **Validate path params** (regex/enums) before they reach upstream URLs.
6. Keep `parsers.py` pure. Anything that needs the network belongs in `client.py`.
7. **A page must never 500 because of data.** Loaders in `web/routes.py` time out after
   4 s and any failure falls back to skeletons + client-side loading.

## Design system ("Seismic Clay" — restrained neumorphism)

Read `docs/design-brief.md` before UI work. The essentials:

- **One material.** Page and surfaces share `--clay`; depth comes only from paired
  shadows. Use the tokens: `--raise`, `--raise-sm`, `--raise-xs` (raised) and `--inset`,
  `--inset-sm` (pressed/wells). Three depths only: raised · inset · flat. Don't nest
  raised inside raised; put rows flat inside a card.
- **Surfaces:** `.card` (raised container), `.well`/`.facts` (inset), `.chip` (inset meta),
  `.pill` (small raised label), `.tile` (raised link). Controls: `.btn` (raised → inset on
  press), `.btn--accent`, `.field` (inset input/select), `.segmented` (inset track + raised
  selected), `.check` (custom checkbox), `.nav` (inset track + raised current item).
- **Colour carries meaning only:** magnitude (`--m-0/3/4/5/6/7` via `data-m` and
  `magBucket()`), tsunami level (`--lv-awas/siaga/waspada`), live/ok (`--ok`), accent
  `--accent` (fills, focus) and `--accent-ink` (text). Never hard-code colours; add a token
  in both light and dark blocks. Any element with `data-m` exposes `--fault`.
- **Contrast:** text must pass WCAG AA on both `--clay` and `--well` (ink tokens are
  pre-checked). Every interactive state needs a non-shadow cue; focus uses the accent ring.
- **Type:** Plus Jakarta Sans (UI) + JetBrains Mono (`.mono`/`.num`, all numbers).
  Sentence-case headings; no uppercase letter-spaced "eyebrow" labels.
- **Images:** shakemaps sit in `.figure` (max-height `min(62vh, 720px)`); thumbnails in
  `.gallery` (4:3, capped width). Keep images lazy and aspect-ratio'd.
- **Icons are SVG only.** Never use text glyphs (arrows, ×, +/−, ↑↓) as icons. Use
  `{{ icon("name") }}` in Jinja, `icon()`/`iconHTML()` from `lib/icons.js` in JS, or the
  `--i-*` CSS mask tokens (chevron, sort, check, close) for pseudo-elements. Add new icons
  to both `web/icons.py` and `lib/icons.js`.
- **Forms:** every control is styled — `.field` inputs (custom search clear icon),
  `.field--select` (chevron; `appearance: base-select` styles the open list in Chromium),
  `.check` (custom checkbox), `.segmented`. Don't ship a native-looking control.
- **Maps:** `createMap()` adds SVG zoom buttons and the custom basemap switcher
  (`BasemapControl`) — don't use `L.control.layers`. Every map marks the most recent event
  with `latestMarker()` (pulsing epicentre + "Terbaru" label).
- **Theme:** light is the default; dark only when chosen with the toggle (stored in
  `localStorage`). Theme changes cross-fade via the `theme-transition` class.
- **Motion:** all animation lives in the "Motion system" block under
  `prefers-reduced-motion: no-preference` — entrance rise/stagger, list fade (until
  `:root.settled`), dial/meter fills via `@starting-style`, dialog/select/menu open-close
  transitions, `details` height transitions. Use `--dur`/`--dur-slow` and `--ease`.
- **Scrollbars:** thin 6px global style in the "Scrollbar" section — don't override per
  component.
- **Responsive:** check 375, 768, 1024, 1440 and 1920+ in light and dark, with no
  horizontal scroll. Grid children need `minmax(0, 1fr)`; prefer container queries for
  component-level layout (see `.hero`).
- Server markup (Jinja macros) and client builders (`lib/ui.js`: `eventItem`, `dial`,
  `magBadge`, `facts`) must produce the **same structure** — change both together.

## Conventions

- Python 3.13, type hints everywhere, Ruff (line length 100).
- API responses: English snake_case keys, numbers as numbers, ISO 8601 datetimes with
  offsets, lists wrapped in `Envelope` (`data` + `meta`). Set `Cache-Control` per route.
- UI copy is **Indonesian**. Times are displayed in **WIB** (`lib/format.js` in the browser,
  `web/format.py` on the server).
- Static URLs in templates are plain paths with `?v={{ asset_version }}` — don't use
  `url_for` (it builds absolute URLs that break behind proxies).
- Pages read embedded data via `initialData()` (`lib/initial.js`), render immediately, then
  refresh with `every(ms, task)` from `lib/api.js`.

## SEO

- Each page: one `<h1>`, unique title/description (home is dynamic: latest magnitude +
  region), canonical, `hreflang="id"`, Open Graph + Twitter (`og.png` 1200×630).
- JSON-LD graph in `web/routes.py::_jsonld`: WebSite + Organization on every page,
  WebPage, BreadcrumbList (non-home), Dataset (about).
- `/sitemap.xml` and `/robots.txt` are generated from `PAGES`; `/api/*` is `noindex`.
- `tests/test_web.py` asserts server-rendered content and SEO tags — extend it for new pages.

## Adding things

- **New page:** add a `Page` to `app/web/pages.py`, a template in `templates/pages/`, an
  optional loader in `LOADERS` (web/routes.py) for server-rendered data, and (if
  interactive) `static/js/pages/<name>.js`. Routes, nav, and sitemap follow.
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
- Some analysis images don't exist for every event; the gallery removes tiles that 404.
- Basemap: Esri Light/Dark Gray Canvas (no key). CARTO now requires an API key.

## Deployment

Vercel detects `app` in `app/main.py`. `pyproject.toml` sets
`[tool.vercel.fastapi.static] cdn = true` so `/static` is served from the CDN.
`vercel.json` holds function limits, bundle excludes, and static cache headers (app
assets 10 min — module imports aren't versioned; vendor files immutable).
