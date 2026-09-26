"""HTML pages, robots.txt, sitemap.xml and the web manifest.

Pages are server-rendered shells; data loads client-side from `/api/v1`.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app import __version__
from app.core.config import get_settings
from app.web.pages import PAGES, PAGES_BY_KEY, SITE_DESCRIPTION, SITE_NAME, Page

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals.update(
    site_name=SITE_NAME,
    nav_pages=[p for p in PAGES if p.in_nav],
    # Cache-busting token for /static URLs: the deployed commit, else the app version.
    asset_version=(os.environ.get("VERCEL_GIT_COMMIT_SHA") or __version__)[:8],
)

router = APIRouter(include_in_schema=False)

_HTML_CACHE = "public, max-age=0, s-maxage=300, stale-while-revalidate=86400"


def _jsonld(page: Page, url: str, origin: str) -> str:
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebPage",
            "@id": url,
            "url": url,
            "name": page.title,
            "description": page.description,
            "inLanguage": "id-ID",
            "isPartOf": {"@id": f"{origin}/#website"},
        }
    ]
    if page.key == "home":
        graph.append(
            {
                "@type": "WebSite",
                "@id": f"{origin}/#website",
                "url": f"{origin}/",
                "name": SITE_NAME,
                "description": SITE_DESCRIPTION,
                "inLanguage": "id-ID",
            }
        )
    else:
        graph.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Beranda", "item": f"{origin}/"},
                    {"@type": "ListItem", "position": 2, "name": page.nav_label, "item": url},
                ],
            }
        )
    # Escape "<" so the payload can never close the <script> element.
    return json.dumps({"@context": "https://schema.org", "@graph": graph}).replace("<", "\\u003c")


def _render(request: Request, page: Page) -> HTMLResponse:
    origin = get_settings().site_origin
    canonical = f"{origin}{page.path}"
    response = templates.TemplateResponse(
        request=request,
        name=page.template,
        context={
            "page": page,
            "canonical": canonical,
            "origin": origin,
            "jsonld": _jsonld(page, canonical, origin),
        },
    )
    response.headers["Cache-Control"] = _HTML_CACHE
    return response


def _page_route(page: Page) -> None:
    async def view(request: Request) -> HTMLResponse:
        return _render(request, page)

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
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f4f3ef",
        "theme_color": "#f4f3ef",
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
    return RedirectResponse(f"/static/img/favicon.ico?v={__version__}", status_code=308)
