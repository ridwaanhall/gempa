# Gempa

Indonesian earthquake monitor — a FastAPI app that proxies and normalises the
official **BMKG** earthquake and tsunami feeds, and serves a fast, responsive
web UI on top of them. Live at [gempa.rone.dev](https://gempa.rone.dev).

- **Terkini** — latest felt earthquake, realtime summary, newest detections
- **Realtime** — ~200 automatic detections with filters, map, and per-event revision history
- **Dirasakan / M5+** — announced earthquakes with shakemaps, analysis images, and BMKG narratives
- **Tsunami** — warning bulletins grouped per earthquake: timeline, warning zones, observed waves
- **Merusak** — catalogue of damaging earthquakes since the 1920s
- **Peta** — seismicity map with 3-month / 5-year catalogues, stations, and fault lines
- **API** — open, documented JSON API at [`/docs`](https://gempa.rone.dev/docs)

## Stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.13, FastAPI, httpx (async), Pydantic v2, Jinja2 |
| Frontend | Hand-written CSS (design tokens, no framework), vanilla ES modules, Leaflet 1.9 (vendored) |
| Tooling | uv, Ruff, pytest + respx |
| Hosting | Vercel (Python runtime, Fluid compute); static assets served from the CDN |

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # then set BMKG_API
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000 (site) and http://localhost:8000/docs (API).

```bash
uv run pytest          # tests (upstream is mocked; no network needed)
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `BMKG_API` | yes | Base URL of the upstream BMKG feed bucket. **Secret** — used server-side only. |
| `SITE_URL` | no | Public origin for canonical URLs and the sitemap. Default `https://gempa.rone.dev`. |
| `DEBUG` | no | FastAPI debug mode. Default `false`. |

The upstream URL never reaches the browser: every feed, image, and narrative is
fetched by the server and re-exposed under `/api/v1`.

## API

All endpoints are `GET`, documented at `/docs` (Swagger UI) and `/redoc`.

| Endpoint | Description |
| --- | --- |
| `/api/v1/earthquakes/latest` | Latest felt earthquake |
| `/api/v1/earthquakes/realtime?min_magnitude=&limit=` | Automatic detections (UTC) |
| `/api/v1/earthquakes/realtime/{event_id}/history` | Revision history of a detection |
| `/api/v1/earthquakes/felt` | Last 30 felt earthquakes |
| `/api/v1/earthquakes/significant` | Last 30 M5+ earthquakes |
| `/api/v1/earthquakes/damaging?year=` | Damaging earthquakes catalogue |
| `/api/v1/earthquakes/archive/{3m,5y}?min_magnitude=` | Reviewed catalogues |
| `/api/v1/earthquakes/{event_id}/narrative` | BMKG press narrative (sanitised HTML) |
| `/api/v1/tsunami` | Tsunami warnings, grouped per earthquake |
| `/api/v1/stations/{indonesia,global}` | Seismic stations |
| `/api/v1/faults/{indonesia,global}` | Fault lines (GeoJSON) |
| `/api/v1/media/{event_id}/{kind}` | Shakemap, analysis and tsunami map images |
| `/api/v1/health` | Liveness |

List responses look like `{"data": [...], "meta": {"count", "source", "generated_at"}}`.
Keys are English, numbers are numbers, coordinates are signed decimal degrees,
and datetimes are ISO 8601 with an explicit offset.

## Deploying to Vercel

1. Import the repository in Vercel (framework preset: FastAPI — auto-detected from `app/main.py`).
2. Set `BMKG_API` (and optionally `SITE_URL`) in *Settings → Environment Variables*.
3. Deploy. `vercel.json` sets function limits and static cache headers.

If the site sits behind Cloudflare, **turn off Rocket Loader** (*Speed → Optimization*)
— it rewrites script tags. The app's own scripts opt out with `data-cfasync="false"`.

## Data & disclaimer

Data © BMKG (Badan Meteorologi, Klimatologi, dan Geofisika). This is an
unofficial project; in an emergency follow BMKG, BNPB, and local BPBD guidance.

## License

[CC0-1.0](LICENSE)
