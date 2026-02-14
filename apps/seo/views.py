"""SEO views — robots.txt and other SEO-specific responses."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views import View


class RobotsTxtView(View):
    """Serve ``robots.txt`` dynamically with sitemap reference."""

    http_method_names = ["get"]

    def get(self, request: HttpRequest) -> HttpResponse:
        site_url = request.build_absolute_uri("/")
        lines = [
            "User-agent: *",
            "Allow: /",
            "",
            "# Disallow API endpoints (JSON data, not user-facing)",
            "Disallow: /api/",
            "",
            f"Sitemap: {site_url}sitemap.xml",
        ]
        return HttpResponse(
            "\n".join(lines),
            content_type="text/plain; charset=utf-8",
        )
