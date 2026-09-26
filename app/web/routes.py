"""HTML pages, robots.txt, sitemap.xml and the web manifest.

Each page server-renders its primary content (crawlable, fast first paint) and
embeds the same data as JSON for the client scripts, which then keep it fresh
from `/api/v1`. If BMKG is slow or down, the page renders skeletons and the
client fetches on its own.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.bmkg.client import BmkgClient, UpstreamError
from app.core.assets import import_map, static_url
from app.core.config import get_settings
from app.web import format as fmt
from app.web.icons import icon
from app.web.pages import PAGES, PAGES_BY_KEY, SITE_DESCRIPTION, SITE_NAME, Page

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters.update(fmt.FILTERS)
templates.env.globals.update(fmt.GLOBALS, icon=icon)
templates.env.globals.update(
    site_name=SITE_NAME,
    nav_pages=[p for p in PAGES if p.in_nav],
    static_url=static_url,
    import_map=import_map,
)

router = APIRouter(include_in_schema=False)

_HTML_CACHE = "public, max-age=0, s-maxage=60, stale-while-revalidate=600"
_SSR_TIMEOUT = 4.0  # seconds; beyond this the client loads the data itself
OG_IMAGE = "/static/img/og.png"


def _dump(value: Any) -> Any:
    if isinstance(value, list):
        return [item.model_dump(mode="json") for item in value]
    return value.model_dump(mode="json")


# ── Per-page data loaders ────────────────────────────────────

Loader = Callable[[BmkgClient], Awaitable[dict[str, Any]]]


async def _home(bmkg: BmkgClient) -> dict[str, Any]:
    latest, realtime = await asyncio.gather(bmkg.latest(), bmkg.realtime())
    return {"latest": _dump(latest), "realtime": _dump(realtime)}


async def _realtime(bmkg: BmkgClient) -> dict[str, Any]:
    return {"events": _dump(await bmkg.realtime())}


async def _felt(bmkg: BmkgClient) -> dict[str, Any]:
    return {"events": _dump(await bmkg.felt())}


async def _significant(bmkg: BmkgClient) -> dict[str, Any]:
    return {"events": _dump(await bmkg.significant())}


async def _tsunami(bmkg: BmkgClient) -> dict[str, Any]:
    return {"events": _dump(await bmkg.tsunami())}


async def _damaging(bmkg: BmkgClient) -> dict[str, Any]:
    # Only the first page is server-rendered; the client loads the full catalogue.
    return {"preview": _dump((await bmkg.damaging())[:25])}


LOADERS: dict[str, Loader] = {
    "home": _home,
    "realtime": _realtime,
    "felt": _felt,
    "significant": _significant,
    "tsunami": _tsunami,
    "damaging": _damaging,
}


async def _load(request: Request, page: Page) -> dict[str, Any] | None:
    loader = LOADERS.get(page.key)
    if loader is None:
        return None
    try:
        return await asyncio.wait_for(loader(request.app.state.bmkg), _SSR_TIMEOUT)
    except (UpstreamError, TimeoutError):
        logger.info("server render without data for %s", page.key)
    except Exception:
        # Never fail a page because of data; the client will load it instead.
        logger.exception("server render failed for %s", page.key)
    return None


# ── SEO ──────────────────────────────────────────────────────


def _seo(page: Page, data: dict[str, Any] | None) -> tuple[str, str]:
    """Title and description; the home page leads with the latest earthquake."""
    if page.key == "home" and data:
        eq = data["latest"]
        title = f"Gempa terkini M{fmt.mag(eq['magnitude'])} {eq['region']}"
        description = (
            f"Gempa M{fmt.mag(eq['magnitude'])} terjadi {fmt.wib_long(eq['origin_time'])}, "
            f"kedalaman {fmt.depth(eq['depth_km'])}, {eq['region']}. "
            "Pantau gempa bumi Indonesia real-time dari data BMKG."
        )
        return title, description
    return page.title, page.description


def _jsonld(page: Page, url: str, origin: str, title: str, description: str) -> str:
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebSite",
            "@id": f"{origin}/#website",
            "url": f"{origin}/",
            "name": SITE_NAME,
            "description": SITE_DESCRIPTION,
            "inLanguage": "id-ID",
            "publisher": {"@id": f"{origin}/#organization"},
        },
        {
            "@type": "Organization",
            "@id": f"{origin}/#organization",
            "name": SITE_NAME,
            "url": f"{origin}/",
            "logo": f"{origin}/static/img/android-chrome-512x512.png",
        },
        {
            "@type": "WebPage",
            "@id": url,
            "url": url,
            "name": title,
            "description": description,
            "inLanguage": "id-ID",
            "isPartOf": {"@id": f"{origin}/#website"},
            "primaryImageOfPage": f"{origin}{OG_IMAGE}",
        },
    ]
    if page.key != "home":
        graph.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Beranda", "item": f"{origin}/"},
                    {"@type": "ListItem", "position": 2, "name": page.nav_label, "item": url},
                ],
            }
        )
    if page.key == "about":
        graph.append(
            {
                "@type": "Dataset",
                "name": "Data gempa bumi dan tsunami Indonesia (BMKG), dinormalisasi",
                "description": (
                    "API JSON terbuka berisi gempa terkini, deteksi real-time, gempa dirasakan, "
                    "gempa M5+, peringatan tsunami, dan katalog gempa merusak dari BMKG."
                ),
                "url": url,
                "isAccessibleForFree": True,
                "license": "https://creativecommons.org/publicdomain/zero/1.0/",
                "creator": {"@id": f"{origin}/#organization"},
                "spatialCoverage": {"@type": "Place", "name": "Indonesia"},
                "distribution": [
                    {
                        "@type": "DataDownload",
                        "encodingFormat": "application/json",
                        "contentUrl": f"{origin}/api/v1/earthquakes/realtime",
                    }
                ],
            }
        )
    # Escape "<" so the payload can never close the <script> element.
    return json.dumps({"@context": "https://schema.org", "@graph": graph}).replace("<", "\\u003c")


async def _render(request: Request, page: Page) -> HTMLResponse:
    origin = get_settings().site_origin
    canonical = f"{origin}{page.path}"
    data = await _load(request, page)
    title, description = _seo(page, data)
    response = templates.TemplateResponse(
        request=request,
        name=page.template,
        context={
            "page": page,
            "title": title,
            "description": description,
            "canonical": canonical,
            "origin": origin,
            "og_image": f"{origin}{OG_IMAGE}",
            "jsonld": _jsonld(page, canonical, origin, title, description),
            "data": data,
        },
    )
    response.headers["Cache-Control"] = _HTML_CACHE
    return response


def _page_route(page: Page) -> None:
    async def view(request: Request) -> HTMLResponse:
        return await _render(request, page)

    router.add_api_route(page.path, view, methods=["GET"], response_class=HTMLResponse,
                         name=f"page:{page.key}")  # fmt: skip


for _page in PAGES:
    _page_route(_page)


@router.get("/dashboard/")
@router.get("/dashboard")
async def legacy_dashboard() -> RedirectResponse:
    return RedirectResponse(PAGES_BY_KEY["map"].path, status_code=301)


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots() -> PlainTextResponse:
    origin = get_settings().site_origin
    body = f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {origin}/sitemap.xml\n"
    return PlainTextResponse(body, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/sitemap.xml")
async def sitemap() -> Response:
    origin = get_settings().site_origin
    today = datetime.now(UTC).date().isoformat()
    urls = "".join(
        f"<url><loc>{origin}{p.path}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>{p.changefreq}</changefreq><priority>{p.priority:.1f}</priority></url>"
        for p in PAGES
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    )
    return Response(xml, media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})  # fmt: skip


@router.get("/site.webmanifest")
async def manifest() -> Response:
    data = {
        "name": f"{SITE_NAME} — Monitor gempa Indonesia",
        "short_name": SITE_NAME,
        "description": SITE_DESCRIPTION,
        "lang": "id",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#e7e1d8",
        "theme_color": "#e7e1d8",
        "icons": [
            {"src": "/static/img/android-chrome-192x192.png", "sizes": "192x192",
             "type": "image/png"},
            {"src": "/static/img/android-chrome-512x512.png", "sizes": "512x512",
             "type": "image/png"},
        ],
    }  # fmt: skip
    return Response(json.dumps(data), media_type="application/manifest+json",
                    headers={"Cache-Control": "public, max-age=86400"})  # fmt: skip


@router.get("/favicon.ico")
async def favicon() -> RedirectResponse:
    return RedirectResponse(static_url("img/favicon.ico"), status_code=308)
