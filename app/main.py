"""FastAPI application. Vercel picks up `app` from this module (app/main.py)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.v1.routes import router as api_v1
from app.bmkg.client import BmkgClient, UpstreamError, UpstreamNotFound
from app.core.cache import TTLCache
from app.core.config import get_settings
from app.core.security import SecurityHeadersMiddleware
from app.schemas import Health
from app.web.routes import router as web_router
from app.web.routes import templates

STATIC_DIR = Path(__file__).resolve().parent / "static"

API_DESCRIPTION = """
Open JSON API over the official earthquake and tsunami feeds of
**BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika), Indonesia's
meteorology and geophysics agency.

* All responses are normalised: English keys, numeric values, signed
  decimal-degree coordinates, and ISO 8601 datetimes with explicit offsets.
* List endpoints return `{"data": [...], "meta": {"count", "source", "generated_at"}}`.
* Responses are cached at the edge for 30 s to 24 h depending on the feed.
* Data belongs to BMKG. This service is unofficial; for emergencies follow
  BMKG, BNPB, and BPBD instructions.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with httpx.AsyncClient(
        timeout=settings.upstream_timeout,
        headers={"User-Agent": f"gempa/{__version__} (+{settings.site_origin})"},
        follow_redirects=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    ) as http:
        app.state.bmkg = BmkgClient(http, settings.bmkg_base, TTLCache())
        yield


def _wants_html(request: Request) -> bool:
    return not request.url.path.startswith("/api/") and "text/html" in request.headers.get(
        "accept", ""
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Gempa API",
        version=__version__,
        summary="Indonesian earthquake & tsunami data from BMKG, normalised.",
        description=API_DESCRIPTION,
        lifespan=lifespan,
        debug=settings.debug,
        openapi_tags=[
            {"name": "earthquakes", "description": "Earthquake events and catalogues."},
            {"name": "tsunami", "description": "Tsunami early-warning bulletins."},
            {"name": "reference", "description": "Seismic stations and fault lines."},
            {"name": "media", "description": "Maps and analysis images."},
            {"name": "system", "description": "Service status."},
        ],
        license_info={"name": "CC0-1.0", "identifier": "CC0-1.0"},
    )
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(UpstreamNotFound)
    async def upstream_not_found(_: Request, exc: UpstreamNotFound) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=404,
                            headers={"Cache-Control": "public, s-maxage=60"})  # fmt: skip

    @app.exception_handler(UpstreamError)
    async def upstream_error(_: Request, exc: UpstreamError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=502,
                            headers={"Cache-Control": "no-store"})  # fmt: skip

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
        if exc.status_code == 404 and _wants_html(request):
            return templates.TemplateResponse(
                request=request, name="pages/404.html", context={"page": None}, status_code=404
            )
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code,
                            headers=getattr(exc, "headers", None))  # fmt: skip

    @app.get("/api/v1/health", tags=["system"], response_model=Health)
    async def health() -> Health:
        return Health(status="ok", version=__version__)

    app.include_router(api_v1, prefix="/api/v1")
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
