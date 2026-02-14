"""Django sitemaps for Gempa Monitor."""

from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap entries for all static front-end pages."""

    protocol = "https"

    _page_items = [
        {"name": "web:dashboard", "priority": 1.0, "changefreq": "always"},
        {"name": "web:realtime", "priority": 0.9, "changefreq": "always"},
        {"name": "web:felt", "priority": 0.8, "changefreq": "hourly"},
        {"name": "web:m5", "priority": 0.8, "changefreq": "hourly"},
        {"name": "web:tsunami", "priority": 0.9, "changefreq": "hourly"},
        {"name": "web:damage", "priority": 0.6, "changefreq": "daily"},
    ]

    def items(self):  # noqa: D401
        return self._page_items

    def location(self, item: dict) -> str:
        return reverse(item["name"])

    def changefreq(self, item: dict) -> str:  # type: ignore[override]
        return item.get("changefreq", "hourly")

    def priority(self, item: dict) -> float:  # type: ignore[override]
        return item.get("priority", 0.8)


# Registry for Django's sitemap framework
sitemaps: dict[str, type[Sitemap]] = {
    "static": StaticViewSitemap,
}
