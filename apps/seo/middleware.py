"""SEO & security middleware — adds HTTP headers for better crawlability and security."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse


class SeoHeadersMiddleware:
    """Add SEO-relevant and security HTTP headers to every response.

    Headers added:
    - ``X-Content-Type-Options: nosniff``
    - ``Referrer-Policy: strict-origin-when-cross-origin``
    - ``Permissions-Policy`` (restrict camera, mic, geolocation, etc.)
    - ``X-Robots-Tag`` (allow indexing on page responses, noindex on API)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response: HttpResponse = self.get_response(request)

        # Security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(self), payment=()"
        )

        # Robots: allow front-end pages, noindex API responses
        if request.path.startswith("/api/"):
            response["X-Robots-Tag"] = "noindex, nofollow"
        else:
            response["X-Robots-Tag"] = "index, follow"

        return response
