"""Backward-compatible re-export - all logic now lives in apps.core.services."""

from apps.core.services.bmkg_client import (  # noqa: F401
    BmkgClient,
    BmkgClientError,
    BmkgEndpoints,
    XmlHelper,
    ValueParser,
)

__all__: list[str] = [
    "BmkgClient",
    "BmkgClientError",
    "BmkgEndpoints",
    "XmlHelper",
    "ValueParser",
]
