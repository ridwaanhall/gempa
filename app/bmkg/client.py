"""Async client for the BMKG feed bucket.

The upstream base URL is secret. Errors raised from here therefore never carry
the URL: `UpstreamError` messages are generic and safe to show to users.
"""

import logging
import re
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx
import nh3

from app.bmkg import parsers
from app.core.cache import TTLCache
from app.schemas import (
    ArchiveEvent,
    ArchivePeriod,
    DamagingEarthquake,
    Earthquake,
    EventHistory,
    FaultScope,
    RealtimeEvent,
    Station,
    StationNetwork,
    TsunamiEvent,
)

logger = logging.getLogger(__name__)


class UpstreamError(Exception):
    """BMKG could not be reached or returned something unusable."""


class UpstreamNotFound(UpstreamError):
    """BMKG does not have the requested resource."""


class Feed(StrEnum):
    """Upstream file names, relative to the secret base URL."""

    latest = "datagempa.json"
    realtime = "live30event.xml"
    felt = "last30feltevent.xml"
    significant = "last30event.xml"
    tsunami = "last30tsunamievent.xml"
    damaging = "katalog_gempa.json"
    archive_3m = "3mgempaQL.json"
    archive_5y = "histori.json"
    stations_indonesia = "sensor_seismic.json"
    stations_global = "sensor_global.json"
    faults_indonesia = "indo_faults_lines.geojson"
    faults_global = "fault_indo_world.geojson"


class MediaKind(StrEnum):
    shakemap = "shakemap"
    location_map = "location-map"
    station_intensity = "station-intensity"
    impact = "impact"
    intensity = "intensity"
    tsunami_zones = "tsunami-zones"
    tsunami_travel_time = "tsunami-travel-time"
    tsunami_sea_height = "tsunami-sea-height"


_MEDIA_PATHS: dict[MediaKind, str] = {
    MediaKind.shakemap: "{id}.mmi.jpg",
    MediaKind.location_map: "{id}_rev/loc_map.png",
    MediaKind.station_intensity: "{id}_rev/stationlist_MMI.jpg",
    MediaKind.impact: "{id}_rev/impact_list.jpg",
    MediaKind.intensity: "{id}_rev/intensity_logo.jpg",
    MediaKind.tsunami_zones: "{id}.wz.png",
    MediaKind.tsunami_travel_time: "{id}.tt.png",
    MediaKind.tsunami_sea_height: "{id}.ssh.png",
}

# How long each feed stays fresh in the in-process cache (seconds).
_TTL: dict[Feed, float] = {
    Feed.latest: 30,
    Feed.realtime: 30,
    Feed.felt: 60,
    Feed.significant: 60,
    Feed.tsunami: 60,
    Feed.damaging: 3600,
    Feed.archive_3m: 900,
    Feed.archive_5y: 3600,
    Feed.stations_indonesia: 86400,
    Feed.stations_global: 86400,
    Feed.faults_indonesia: 86400,
    Feed.faults_global: 86400,
}

MAX_MEDIA_BYTES = 8 * 1024 * 1024

_NARRATIVE_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "ol", "ul", "li",
    "h3", "h4", "h5", "table", "thead", "tbody", "tr", "td", "th", "span", "sup", "sub",
}  # fmt: skip


def media_path(kind: MediaKind, event_id: str) -> str:
    return f"/api/v1/media/{event_id}/{kind.value}"


def _media_url(event_id: str, kind: str) -> str:
    return media_path(MediaKind(kind), event_id)


@dataclass(slots=True)
class Media:
    content: bytes
    content_type: str


class BmkgClient:
    def __init__(self, http: httpx.AsyncClient, base_url: str, cache: TTLCache) -> None:
        self._http = http
        self._base = base_url.rstrip("/")
        self._cache = cache

    # ── Transport ────────────────────────────────────────────

    async def _get(self, path: str, *, bust: bool = True) -> httpx.Response:
        url = f"{self._base}/{path}"
        params = {"t": str(int(time.time() // 30))} if bust else None
        try:
            response = await self._http.get(url, params=params)
        except httpx.HTTPError as exc:
            logger.warning("upstream request failed: %s (%s)", path, type(exc).__name__)
            raise UpstreamError("Data BMKG sedang tidak dapat dijangkau.") from None
        if response.status_code in (403, 404):
            raise UpstreamNotFound("Data tidak tersedia.")
        if response.status_code >= 400:
            logger.warning("upstream returned %s for %s", response.status_code, path)
            raise UpstreamError("Data BMKG sedang tidak dapat dijangkau.")
        return response

    async def _feed(self, feed: Feed) -> httpx.Response:
        return await self._get(feed.value)

    async def _cached[T](self, key: str, ttl: float, build) -> T:
        try:
            return await self._cache.get_or_set(key, ttl, build)
        except parsers.ParseError as exc:
            logger.warning("upstream payload unparseable for %s: %s", key, exc)
            raise UpstreamError("Format data BMKG tidak dikenali.") from None

    async def _json(self, feed: Feed) -> Any:
        response = await self._feed(feed)
        try:
            return response.json()
        except ValueError:
            raise parsers.ParseError("invalid JSON") from None

    # ── Feeds ────────────────────────────────────────────────

    async def latest(self) -> Earthquake:
        async def build() -> Earthquake:
            return parsers.parse_latest(await self._json(Feed.latest), _media_url)

        return await self._cached("latest", _TTL[Feed.latest], build)

    async def realtime(self) -> list[RealtimeEvent]:
        async def build() -> list[RealtimeEvent]:
            return parsers.parse_realtime((await self._feed(Feed.realtime)).content)

        return await self._cached("realtime", _TTL[Feed.realtime], build)

    async def felt(self) -> list[Earthquake]:
        async def build() -> list[Earthquake]:
            return parsers.parse_alert_list((await self._feed(Feed.felt)).content, _media_url)

        return await self._cached("felt", _TTL[Feed.felt], build)

    async def significant(self) -> list[Earthquake]:
        async def build() -> list[Earthquake]:
            content = (await self._feed(Feed.significant)).content
            return parsers.parse_alert_list(content, _media_url)

        return await self._cached("significant", _TTL[Feed.significant], build)

    async def tsunami(self) -> list[TsunamiEvent]:
        async def build() -> list[TsunamiEvent]:
            return parsers.parse_tsunami((await self._feed(Feed.tsunami)).content, _media_url)

        return await self._cached("tsunami", _TTL[Feed.tsunami], build)

    async def damaging(self) -> list[DamagingEarthquake]:
        async def build() -> list[DamagingEarthquake]:
            return parsers.parse_damaging(await self._json(Feed.damaging))

        return await self._cached("damaging", _TTL[Feed.damaging], build)

    async def archive(self, period: ArchivePeriod) -> list[ArchiveEvent]:
        feed = Feed.archive_3m if period is ArchivePeriod.three_months else Feed.archive_5y

        async def build() -> list[ArchiveEvent]:
            return parsers.parse_archive(await self._json(feed))

        return await self._cached(f"archive:{period.value}", _TTL[feed], build)

    async def stations(self, network: StationNetwork) -> list[Station]:
        indonesia = network is StationNetwork.indonesia
        feed = Feed.stations_indonesia if indonesia else Feed.stations_global

        async def build() -> list[Station]:
            return parsers.parse_stations(await self._json(feed), network=network.value)

        return await self._cached(f"stations:{network.value}", _TTL[feed], build)

    async def faults(self, scope: FaultScope) -> dict[str, Any]:
        feed = Feed.faults_indonesia if scope is FaultScope.indonesia else Feed.faults_global

        async def build() -> dict[str, Any]:
            return parsers.parse_faults(await self._json(feed))

        return await self._cached(f"faults:{scope.value}", _TTL[feed], build)

    async def history(self, event_id: str) -> EventHistory:
        async def build() -> EventHistory:
            response = await self._get(f"history.{event_id}.txt")
            return parsers.parse_history(event_id, response.text)

        return await self._cached(f"history:{event_id}", 60, build)

    async def narrative(self, event_id: str) -> str:
        async def build() -> str:
            response = await self._get(f"{event_id}_narasi.txt")
            html = nh3.clean(
                response.text,
                tags=_NARRATIVE_TAGS,
                attributes={"td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}},
                url_schemes=set(),
            )
            # BMKG pads its HTML with empty paragraphs; drop them.
            html = re.sub(r"<p>(?:\s|&nbsp;|<br\s*/?>)*</p>", "", html).strip()
            if not html:
                raise UpstreamNotFound("Narasi tidak tersedia.")
            return html

        return await self._cached(f"narrative:{event_id}", 600, build)

    async def media(self, event_id: str, kind: MediaKind) -> Media:
        response = await self._get(_MEDIA_PATHS[kind].format(id=event_id), bust=False)
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if not content_type.startswith("image/") or len(response.content) > MAX_MEDIA_BYTES:
            raise UpstreamNotFound("Gambar tidak tersedia.")
        return Media(content=response.content, content_type=content_type)
