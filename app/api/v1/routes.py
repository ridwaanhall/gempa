"""Public JSON API, version 1.

Every list endpoint returns `{"data": [...], "meta": {...}}`. Responses carry
`Cache-Control` so Vercel's CDN absorbs most traffic.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, Response

from app.api.deps import Bmkg
from app.bmkg.client import MediaKind
from app.schemas import (
    ArchiveEvent,
    ArchivePeriod,
    DamagingEarthquake,
    Earthquake,
    Envelope,
    EventHistory,
    FaultScope,
    Meta,
    Narrative,
    Problem,
    RealtimeEvent,
    Station,
    StationNetwork,
    TsunamiEvent,
)

router = APIRouter(
    responses={
        502: {"model": Problem, "description": "BMKG is unreachable or returned bad data."},
    }
)

NOT_FOUND = {404: {"model": Problem, "description": "BMKG has no such resource."}}

BMKG_EVENT_ID = r"^\d{14}$"
REALTIME_EVENT_ID = r"^[a-z]{3}\d{4}[a-z0-9]{3,6}$"


def _cache(response: Response, seconds: int) -> None:
    response.headers["Cache-Control"] = (
        f"public, max-age={min(seconds, 60)}, s-maxage={seconds}, "
        f"stale-while-revalidate={seconds * 5}"
    )


def _envelope[T](items: list[T]) -> Envelope[list[T]]:
    return Envelope(data=items, meta=Meta(count=len(items), generated_at=datetime.now(UTC)))


# ── Earthquakes ──────────────────────────────────────────────


@router.get(
    "/earthquakes/latest",
    tags=["earthquakes"],
    summary="Latest felt earthquake",
    response_model=Envelope[Earthquake],
)
async def latest(bmkg: Bmkg, response: Response) -> Envelope[Earthquake]:
    """The most recent earthquake BMKG announced as felt by the public."""
    _cache(response, 30)
    return Envelope(data=await bmkg.latest(), meta=Meta(count=1, generated_at=datetime.now(UTC)))


@router.get(
    "/earthquakes/realtime",
    tags=["earthquakes"],
    summary="Real-time detections",
    response_model=Envelope[list[RealtimeEvent]],
)
async def realtime(
    bmkg: Bmkg,
    response: Response,
    min_magnitude: Annotated[float, Query(ge=0, le=10)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> Envelope[list[RealtimeEvent]]:
    """Automatic detections from the BMKG network (Indonesia and surroundings), newest first.

    Unreviewed: magnitudes and locations may be revised. Times are UTC.
    """
    _cache(response, 30)
    events = [e for e in await bmkg.realtime() if e.magnitude >= min_magnitude]
    return _envelope(events[:limit])


@router.get(
    "/earthquakes/realtime/{event_id}/history",
    tags=["earthquakes"],
    summary="Revision history of a real-time event",
    response_model=EventHistory,
    responses=NOT_FOUND,
)
async def realtime_history(
    bmkg: Bmkg,
    response: Response,
    event_id: Annotated[str, Path(pattern=REALTIME_EVENT_ID, examples=["bmg2026swgz"])],
) -> EventHistory:
    """Each automatic re-computation of the solution as more stations report in."""
    _cache(response, 60)
    return await bmkg.history(event_id)


@router.get(
    "/earthquakes/felt",
    tags=["earthquakes"],
    summary="Recent felt earthquakes",
    response_model=Envelope[list[Earthquake]],
)
async def felt(bmkg: Bmkg, response: Response) -> Envelope[list[Earthquake]]:
    """The last 30 earthquakes felt by the public, with MMI felt reports. Times are WIB."""
    _cache(response, 60)
    return _envelope(await bmkg.felt())


@router.get(
    "/earthquakes/significant",
    tags=["earthquakes"],
    summary="Recent M5+ earthquakes",
    response_model=Envelope[list[Earthquake]],
)
async def significant(bmkg: Bmkg, response: Response) -> Envelope[list[Earthquake]]:
    """The last 30 earthquakes of magnitude 5.0 or greater. Times are WIB."""
    _cache(response, 60)
    return _envelope(await bmkg.significant())


@router.get(
    "/earthquakes/damaging",
    tags=["earthquakes"],
    summary="Damaging earthquakes catalogue",
    response_model=Envelope[list[DamagingEarthquake]],
)
async def damaging(
    bmkg: Bmkg,
    response: Response,
    year: Annotated[int | None, Query(ge=1800, le=2100)] = None,
) -> Envelope[list[DamagingEarthquake]]:
    """Historical earthquakes in Indonesia that caused casualties or damage."""
    _cache(response, 3600)
    events = await bmkg.damaging()
    if year is not None:
        events = [e for e in events if e.origin_time.year == year]
    return _envelope(events)


@router.get(
    "/earthquakes/archive/{period}",
    tags=["earthquakes"],
    summary="Reviewed catalogue",
    response_model=Envelope[list[ArchiveEvent]],
)
async def archive(
    bmkg: Bmkg,
    response: Response,
    period: ArchivePeriod,
    min_magnitude: Annotated[float, Query(ge=0, le=10)] = 0,
) -> Envelope[list[ArchiveEvent]]:
    """`3m`: last 3 months (M4.5+). `5y`: last 5 years (M5+). Times are UTC."""
    _cache(response, 900)
    events = [e for e in await bmkg.archive(period) if e.magnitude >= min_magnitude]
    return _envelope(events)


@router.get(
    "/earthquakes/{event_id}/narrative",
    tags=["earthquakes"],
    summary="BMKG press narrative",
    response_model=Narrative,
    responses=NOT_FOUND,
)
async def narrative(
    bmkg: Bmkg,
    response: Response,
    event_id: Annotated[str, Path(pattern=BMKG_EVENT_ID, examples=["20260922065106"])],
) -> Narrative:
    """BMKG's written analysis (Indonesian), sanitised. Usually only for M5+ events."""
    _cache(response, 600)
    return Narrative(event_id=event_id, html=await bmkg.narrative(event_id))


# ── Tsunami ──────────────────────────────────────────────────


@router.get(
    "/tsunami",
    tags=["tsunami"],
    summary="Tsunami warnings",
    response_model=Envelope[list[TsunamiEvent]],
)
async def tsunami(bmkg: Bmkg, response: Response) -> Envelope[list[TsunamiEvent]]:
    """Recent tsunami early-warning bulletins, grouped per earthquake, newest first."""
    _cache(response, 60)
    return _envelope(await bmkg.tsunami())


# ── Reference layers ─────────────────────────────────────────


@router.get(
    "/stations/{network}",
    tags=["reference"],
    summary="Seismic stations",
    response_model=Envelope[list[Station]],
)
async def stations(
    bmkg: Bmkg, response: Response, network: StationNetwork
) -> Envelope[list[Station]]:
    """Seismograph stations of the BMKG (`indonesia`) or partner (`global`) network."""
    _cache(response, 86400)
    return _envelope(await bmkg.stations(network))


@router.get(
    "/faults/{scope}",
    tags=["reference"],
    summary="Active fault lines (GeoJSON)",
    response_description="A GeoJSON FeatureCollection of LineStrings.",
)
async def faults(bmkg: Bmkg, response: Response, scope: FaultScope) -> dict[str, Any]:
    """Fault traces for Indonesia, or Indonesia plus global plate boundaries."""
    _cache(response, 86400)
    return await bmkg.faults(scope)


# ── Media ────────────────────────────────────────────────────


@router.get(
    "/media/{event_id}/{kind}",
    tags=["media"],
    summary="Event image",
    response_class=Response,
    responses={200: {"content": {"image/png": {}, "image/jpeg": {}}}, **NOT_FOUND},
)
async def media(
    bmkg: Bmkg,
    event_id: Annotated[str, Path(pattern=BMKG_EVENT_ID)],
    kind: MediaKind,
) -> Response:
    """Shakemap, analysis, and tsunami maps for an event, proxied from BMKG."""
    item = await bmkg.media(event_id, kind)
    return Response(
        content=item.content,
        media_type=item.content_type,
        headers={"Cache-Control": "public, max-age=3600, s-maxage=86400"},
    )
