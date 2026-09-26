"""Security and crawler headers, as a pure ASGI middleware (no body buffering)."""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.assets import import_map_csp_hash

_TILE_HOSTS = "https://tile.openstreetmap.org https://server.arcgisonline.com"
# Cloudflare (in front of gempa.rone.dev) may inject its analytics beacon.
_CF = "https://static.cloudflareinsights.com"

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        # The hash admits only the inline import map (see core/assets.py).
        f"script-src 'self' {import_map_csp_hash()} {_CF}",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        f"img-src 'self' data: {_TILE_HOSTS}",
        "connect-src 'self' https://cloudflareinsights.com",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

_BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}

# Swagger UI / ReDoc ship inline scripts and CDN assets; don't apply our CSP there.
_DOCS_PATHS = ("/docs", "/redoc")


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in _BASE_HEADERS.items():
                    headers.setdefault(name, value)
                if not path.startswith(_DOCS_PATHS):
                    headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
                if path.startswith(("/api/", "/docs", "/redoc", "/openapi.json")):
                    headers.setdefault("X-Robots-Tag", "noindex")
            await send(message)

        await self.app(scope, receive, send_with_headers)
