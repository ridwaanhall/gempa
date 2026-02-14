"""Django context processor — injects SEO metadata into every template context."""

from __future__ import annotations

import json

from django.http import HttpRequest

from .meta import (
    PAGE_META,
    SITE_AUTHOR,
    SITE_DESCRIPTION,
    SITE_KEYWORDS,
    SITE_LOCALE,
    SITE_NAME,
    SITE_OG_TYPE,
    SITE_THEME_COLOR,
    SITE_TWITTER_CARD,
    build_breadcrumb_jsonld,
    build_webpage_jsonld,
    build_website_jsonld,
)


def seo_context(request: HttpRequest) -> dict:
    """Add SEO variables to every template context.

    Relies on ``nav_active`` being set by ``BasePageView.get_context_data``.
    Falls back to site-wide defaults when the current page has no specific meta.
    """
    site_url = request.build_absolute_uri("/")
    page_url = request.build_absolute_uri()

    # Resolve per-page overrides (nav_active is injected later by the view,
    # but we can read the URL path to match a page key).
    page_key = _resolve_page_key(request.path)
    page_meta = PAGE_META.get(page_key, {})

    title = page_meta.get("title", SITE_NAME)
    description = page_meta.get("description", SITE_DESCRIPTION)
    keywords = page_meta.get("keywords", SITE_KEYWORDS)

    # Structured data
    jsonld_parts: list[dict] = []
    if page_key == "dashboard":
        jsonld_parts.append(build_website_jsonld(site_url))

    jsonld_parts.append(
        build_webpage_jsonld(site_url, page_url, title, description)
    )

    # Breadcrumbs
    breadcrumbs = [("Beranda", "")]
    if page_key and page_key != "dashboard":
        breadcrumbs.append((title, request.path.lstrip("/")))
    jsonld_parts.append(build_breadcrumb_jsonld(site_url, breadcrumbs))

    return {
        # Core meta
        "seo_title": f"{title} — {SITE_NAME}",
        "seo_description": description,
        "seo_keywords": keywords,
        "seo_author": SITE_AUTHOR,
        "seo_canonical": page_url,
        # Open Graph
        "seo_og_type": SITE_OG_TYPE,
        "seo_og_locale": SITE_LOCALE,
        "seo_og_site_name": SITE_NAME,
        # Twitter
        "seo_twitter_card": SITE_TWITTER_CARD,
        # Theme
        "seo_theme_color": SITE_THEME_COLOR,
        # JSON-LD (pre-serialised)
        "seo_jsonld": json.dumps(jsonld_parts, ensure_ascii=False),
    }


# ── Helpers ──────────────────────────────────────────────────

_PATH_MAP: dict[str, str] = {
    "/": "dashboard",
    "/realtime/": "realtime",
    "/felt/": "felt",
    "/m5/": "m5",
    "/tsunami/": "tsunami",
    "/damage/": "damage",
}


def _resolve_page_key(path: str) -> str:
    """Map a request path to a PAGE_META key."""
    return _PATH_MAP.get(path, "")
