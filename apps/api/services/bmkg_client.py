from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict, cast
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

import requests
from requests import Response, Session
from time import time
import xml.etree.ElementTree as ET


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


class RealtimeEventDict(TypedDict):
    eventid: str
    status: str
    waktu: str
    lintang: str
    bujur: str
    dalam: str
    mag: str
    fokal: str
    area: str


class RealtimeCatalogDict(TypedDict):
    events: list[RealtimeEventDict]


class BmkgClientError(Exception):
    """Raised when the BMKG API cannot be reached or returns invalid data."""


@dataclass(slots=True, frozen=True)
class BmkgEndpoints:
    """Endpoint configuration for the BMKG client."""

    alert_url: str
    catalog_url: str
    realtime_url: str


class BmkgClient:
    """Lightweight, typed client for retrieving BMKG earthquake data."""

    def __init__(self, endpoints: BmkgEndpoints, session: Session | None = None, timeout: float = 8.0) -> None:
        self._endpoints = endpoints
        self._session: Session = session or requests.Session()
        self._timeout = timeout
        self._session.headers.setdefault("User-Agent", "ridwaanhall-com/1.0")

    def get_alert(self) -> AlertDict:
        """Return the most recent felt earthquake alert."""
        return cast(AlertDict, self._get_json(self._endpoints.alert_url))

    def get_catalog(self) -> CatalogDict:
        """Return the catalog of recent earthquakes."""
        return cast(CatalogDict, self._get_json(self._endpoints.catalog_url))

    def get_realtime(self) -> RealtimeCatalogDict:
        """Return realtime earthquakes converted from XML to JSON."""
        xml_text = self._get_text(self._endpoints.realtime_url)
        events = self._parse_realtime_xml(xml_text)
        return {"events": events}

    def _get_json(self, url: str) -> dict[str, Any]:
        cache_busted_url = self._with_cache_buster(url)

        try:
            response: Response = self._session.get(cache_busted_url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network exceptions
            raise BmkgClientError("Failed to fetch earthquake data") from exc

        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:  # pragma: no cover - invalid json
            raise BmkgClientError("Invalid earthquake data format") from exc

        return data

    def _get_text(self, url: str) -> str:
        cache_busted_url = self._with_cache_buster(url)

        try:
            response: Response = self._session.get(cache_busted_url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover
            raise BmkgClientError("Failed to fetch realtime earthquake data") from exc

        return response.text

    def _parse_realtime_xml(self, xml_text: str) -> list[RealtimeEventDict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise BmkgClientError("Invalid realtime earthquake data format") from exc

        events: list[RealtimeEventDict] = []
        for gempa in root.findall("gempa"):
            events.append(
                {
                    "eventid": (gempa.findtext("eventid") or "").strip(),
                    "status": (gempa.findtext("status") or "").strip(),
                    "waktu": (gempa.findtext("waktu") or "").strip(),
                    "lintang": (gempa.findtext("lintang") or "").strip(),
                    "bujur": (gempa.findtext("bujur") or "").strip(),
                    "dalam": (gempa.findtext("dalam") or "").strip(),
                    "mag": (gempa.findtext("mag") or "").strip(),
                    "fokal": (gempa.findtext("fokal") or "").strip(),
                    "area": (gempa.findtext("area") or "").strip(),
                }
            )

        return events

    def _with_cache_buster(self, url: str) -> str:
        """Append a timestamp query param so BMKG responses are not cached."""
        split_url = urlsplit(url)
        query_params = dict(parse_qsl(split_url.query))
        query_params["t"] = str(int(time() * 1000))
        new_query = urlencode(query_params)
        return urlunsplit((split_url.scheme, split_url.netloc, split_url.path, new_query, split_url.fragment))


__all__ = [
    "AlertDict",
    "BmkgClient",
    "BmkgClientError",
    "BmkgEndpoints",
    "CatalogDict",
    "FeatureDict",
    "GeometryDict",
    "InfoDict",
    "PointDict",
    "PropertiesDict",
    "RealtimeCatalogDict",
    "RealtimeEventDict",
]
