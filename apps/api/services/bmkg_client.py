from __future__ import annotations

from typing import Any, TypedDict

import requests
from requests import Response, Session

DATAGEMPA_URL = "https://bmkg-content-inatews.storage.googleapis.com/datagempa.json?t=1770383949414"
KATALOG_GEMPA_URL = "https://bmkg-content-inatews.storage.googleapis.com/katalog_gempa.json?t=1770383949414"


class PointDict(TypedDict):
    coordinates: str


class InfoDict(TypedDict):
    event: str
    date: str
    time: str
    point: PointDict
    latitude: str
    longitude: str
    magnitude: str
    depth: str
    area: str
    eventid: str
    potential: str
    subject: str
    headline: str
    description: str
    instruction: str
    shakemap: str
    felt: str
    timesent: str


class AlertDict(TypedDict):
    identifier: str
    sender: str
    sent: str
    status: str
    msgType: str
    scope: str
    code: str
    info: InfoDict


class GeometryDict(TypedDict):
    type: str
    coordinates: list[str]


class PropertiesDict(TypedDict):
    lokasi: str
    ot_utc: str
    pusat_gempa: str
    tsunami: str
    id_event: str
    korban_kerusakan: str
    depth: str
    mag: str
    date: str
    sumber: str
    dirasakan: str


class FeatureDict(TypedDict):
    geometry: GeometryDict
    type: str
    properties: PropertiesDict


class CatalogDict(TypedDict):
    type: str
    features: list[FeatureDict]


class BmkgClientError(Exception):
    """Raised when the BMKG API cannot be reached or returns invalid data."""


class BmkgClient:
    """Lightweight client for retrieving BMKG earthquake data."""

    def __init__(self, session: Session | None = None, timeout: float = 8.0) -> None:
        self._session: Session = session or requests.Session()
        self._timeout = timeout
        self._session.headers.setdefault("User-Agent", "gempa-api/1.0")

    def get_alert(self) -> AlertDict:
        """Return the most recent felt earthquake alert."""
        return self._get_json(DATAGEMPA_URL)

    def get_catalog(self) -> CatalogDict:
        """Return the catalog of recent earthquakes."""
        return self._get_json(KATALOG_GEMPA_URL)

    def _get_json(self, url: str) -> dict[str, Any]:
        try:
            response: Response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network exceptions
            raise BmkgClientError(f"Failed to fetch data from {url}") from exc

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:  # pragma: no cover - invalid json
            raise BmkgClientError(f"Invalid JSON returned by {url}") from exc

        return data


__all__ = [
    "AlertDict",
    "BmkgClient",
    "BmkgClientError",
    "CatalogDict",
    "DATAGEMPA_URL",
    "FeatureDict",
    "GeometryDict",
    "InfoDict",
    "KATALOG_GEMPA_URL",
    "PointDict",
    "PropertiesDict",
]
