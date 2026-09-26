"""Pure functions turning raw BMKG payloads into `app.schemas` models.

Nothing here does I/O, so every parser is unit-testable with fixture files.
"""

import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from app.schemas import (
    ArchiveEvent,
    DamagingEarthquake,
    Earthquake,
    EventHistory,
    EventMedia,
    FeltReport,
    HistoryRecord,
    RealtimeEvent,
    Station,
    TsunamiBulletin,
    TsunamiEvent,
    TsunamiMedia,
    WarningZone,
    WaveObservation,
)


class ParseError(ValueError):
    """Upstream payload did not have the expected shape."""


# Indonesian time zones used in BMKG bulletins.
_TZ = {
    "WIB": timezone(timedelta(hours=7)),
    "WITA": timezone(timedelta(hours=8)),
    "WIT": timezone(timedelta(hours=9)),
    "UTC": UTC,
}
WIB = _TZ["WIB"]

LEVEL_RANK = {"AWAS": 3, "SIAGA": 2, "WASPADA": 1}

MediaUrl = Callable[[str, str], str]
"""(event_id, kind) -> public URL of our media proxy."""


# ── Primitive helpers ────────────────────────────────────────


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    number = float(match.group().replace(",", "."))
    return number if math.isfinite(number) else None


def to_int(value: Any) -> int | None:
    number = to_float(value)
    return int(number) if number is not None else None


def _required_float(value: Any, field: str) -> float:
    number = to_float(value)
    if number is None:
        raise ParseError(f"missing numeric field: {field}")
    return number


def _tz_from(text: str) -> timezone:
    for name in ("WITA", "WIT", "WIB", "UTC"):
        if name in text.upper():
            return _TZ[name]
    return WIB


def parse_local_datetime(date_text: str, time_text: str) -> datetime | None:
    """Parse BMKG `dd-mm-yy[yy]` + `HH:MM[:SS] WIB` into an aware datetime."""
    date_text, time_text = (date_text or "").strip(), (time_text or "").strip()
    if not date_text or not time_text:
        return None
    tz = _tz_from(time_text)
    clock = re.sub(r"[A-Za-z\s]+$", "", time_text).strip()
    for date_fmt in ("%d-%m-%y", "%d-%m-%Y"):
        for time_fmt in ("%H:%M:%S", "%H:%M"):
            try:
                naive = datetime.strptime(f"{date_text} {clock}", f"{date_fmt} {time_fmt}")
            except ValueError:
                continue
            return naive.replace(tzinfo=tz)
    return None


def parse_sent(text: str) -> datetime | None:
    """Parse `26/09/2026 02:44:29WIB`."""
    text = (text or "").strip()
    match = re.match(r"(\d{2})/(\d{2})/(\d{4})\s*(\d{2}:\d{2}:\d{2})\s*([A-Z]*)", text)
    if not match:
        return None
    day, month, year, clock, zone = match.groups()
    naive = datetime.strptime(f"{year}-{month}-{day} {clock}", "%Y-%m-%d %H:%M:%S")
    return naive.replace(tzinfo=_TZ.get(zone or "WIB", WIB))


def parse_utc(text: str) -> datetime:
    """Parse `2026/09/26  08:10:21.751` or `2026-09-25 19:39:30.668563` as UTC."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip()).replace("/", "-")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    raise ParseError(f"unrecognised timestamp: {text!r}")


def parse_point(text: str) -> tuple[float, float]:
    """CAP `<point><coordinates>lon,lat</coordinates>` → (lat, lon)."""
    parts = [p.strip() for p in (text or "").split(",")]
    if len(parts) < 2:
        raise ParseError("invalid point")
    lon, lat = _required_float(parts[0], "lon"), _required_float(parts[1], "lat")
    return lat, lon


def signed_coordinate(text: str) -> float | None:
    """`8.23 LS` → -8.23, `4.74 LU` → 4.74, `120.31 BT` → 120.31, `x BB` → -x."""
    number = to_float(text)
    if number is None:
        return None
    suffix = (text or "").strip().upper().split()[-1] if (text or "").strip() else ""
    return -abs(number) if suffix in {"LS", "BB", "S", "W"} else number


# ── XML ──────────────────────────────────────────────────────


def xml_root(text: str | bytes) -> ET.Element:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ParseError("invalid XML") from exc
    for element in root.iter():
        if isinstance(element.tag, str) and "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]
    return root


def _text(node: ET.Element | None, tag: str) -> str:
    if node is None:
        return ""
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""


# ── Alert feeds (latest / felt / M5+) ────────────────────────


def _event_media(event_id: str, media_url: MediaUrl, *, analysis: bool) -> EventMedia:
    if not analysis:
        return EventMedia(shakemap=media_url(event_id, "shakemap"))
    return EventMedia(
        shakemap=media_url(event_id, "shakemap"),
        location_map=media_url(event_id, "location-map"),
        station_intensity=media_url(event_id, "station-intensity"),
        impact=media_url(event_id, "impact"),
        intensity=media_url(event_id, "intensity"),
    )


def earthquake_from_info(info: dict[str, Any], media_url: MediaUrl) -> Earthquake:
    """Build an Earthquake from a CAP `<info>` block (as a flat dict)."""
    event_id = str(info.get("eventid", "")).strip()
    if not event_id:
        raise ParseError("missing eventid")
    point = info.get("point") or {}
    coordinates = point.get("coordinates") if isinstance(point, dict) else None
    if coordinates:
        lat, lon = parse_point(coordinates)
    else:
        lat = signed_coordinate(info.get("latitude", "")) or 0.0
        lon = signed_coordinate(info.get("longitude", "")) or 0.0
    origin = parse_local_datetime(info.get("date", ""), info.get("time", ""))
    if origin is None:
        raise ParseError(f"invalid origin time for {event_id}")
    magnitude = _required_float(info.get("magnitude"), "magnitude")
    potential = str(info.get("potential", "")).strip()
    lowered = potential.lower()
    tsunami = "tsunami" in lowered and "tidak" not in lowered
    felt = str(info.get("felt", "")).strip() or None
    has_shakemap = bool(str(info.get("shakemap", "")).strip())
    return Earthquake(
        event_id=event_id,
        origin_time=origin,
        magnitude=magnitude,
        depth_km=to_float(info.get("depth")) or 0.0,
        latitude=lat,
        longitude=lon,
        region=str(info.get("area", "")).strip(),
        tsunami_potential=tsunami,
        potential=potential,
        felt=felt,
        instruction=str(info.get("instruction", "")).strip() or None,
        has_narrative=magnitude >= 5.0 or tsunami,
        media=_event_media(event_id, media_url, analysis=has_shakemap)
        if has_shakemap
        else EventMedia(),
    )


def _info_dict(info: ET.Element) -> dict[str, Any]:
    data: dict[str, Any] = {child.tag: (child.text or "").strip() for child in info}
    data["point"] = {"coordinates": _text(info.find("point"), "coordinates")}
    return data


def parse_latest(payload: dict[str, Any], media_url: MediaUrl) -> Earthquake:
    info = payload.get("info")
    if not isinstance(info, dict):
        raise ParseError("latest feed has no info block")
    return earthquake_from_info(info, media_url)


def parse_alert_list(xml_text: str | bytes, media_url: MediaUrl) -> list[Earthquake]:
    root = xml_root(xml_text)
    events = []
    for info in root.findall("info"):
        try:
            events.append(earthquake_from_info(_info_dict(info), media_url))
        except ParseError:
            continue
    return sorted(events, key=lambda e: e.origin_time, reverse=True)


# ── Real-time ────────────────────────────────────────────────


def parse_realtime(xml_text: str | bytes) -> list[RealtimeEvent]:
    root = xml_root(xml_text)
    events = []
    for node in root.findall("gempa"):
        try:
            events.append(
                RealtimeEvent(
                    event_id=_text(node, "eventid"),
                    origin_time=parse_utc(_text(node, "waktu")),
                    magnitude=_required_float(_text(node, "mag"), "mag"),
                    depth_km=to_float(_text(node, "dalam")) or 0.0,
                    latitude=_required_float(_text(node, "lintang"), "lintang"),
                    longitude=_required_float(_text(node, "bujur"), "bujur"),
                    region=_text(node, "area"),
                    status=_text(node, "status") or "unknown",
                    has_focal_mechanism=_text(node, "fokal").lower() == "mt_yes",
                )
            )
        except ParseError:
            continue
    return sorted(events, key=lambda e: e.origin_time, reverse=True)


def parse_history(event_id: str, text: str) -> EventHistory:
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 10:
            continue
        try:
            timestamp = parse_utc(parts[0])
        except ParseError:
            continue
        records.append(
            HistoryRecord(
                timestamp=timestamp,
                minutes_after_origin=to_float(parts[1]),
                latitude=to_float(parts[2]),
                longitude=to_float(parts[3]),
                depth_km=to_float(parts[4]),
                phase_count=to_int(parts[5]),
                magnitude_type=parts[6] or None,
                magnitude=to_float(parts[7]),
                magnitude_count=to_int(parts[8]),
                status=parts[9] or None,
            )
        )
    return EventHistory(event_id=event_id, records=records)


# ── GeoJSON catalogues ───────────────────────────────────────


def _features(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return payload["features"]
    raise ParseError("expected a GeoJSON FeatureCollection")


def _lon_lat(feature: dict[str, Any]) -> tuple[float, float]:
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    if len(coords) < 2:
        raise ParseError("feature without coordinates")
    return _required_float(coords[0], "lon"), _required_float(coords[1], "lat")


def parse_archive(payload: Any) -> list[ArchiveEvent]:
    events = []
    for feature in _features(payload):
        props = feature.get("properties") or {}
        try:
            lon, lat = _lon_lat(feature)
            events.append(
                ArchiveEvent(
                    event_id=str(props.get("id", "")),
                    origin_time=parse_utc(str(props.get("time", ""))),
                    magnitude=round(_required_float(props.get("mag"), "mag"), 1),
                    depth_km=round(to_float(props.get("depth")) or 0.0, 1),
                    latitude=lat,
                    longitude=lon,
                    region=str(props.get("place", "")).strip(),
                    phase_count=to_int(props.get("fase")),
                    status=str(props.get("status", "")),
                )
            )
        except ParseError:
            continue
    return sorted(events, key=lambda e: e.origin_time, reverse=True)


_FELT_ITEM = re.compile(r"^\s*([IVX]+(?:\s*-\s*[IVX]+)?)\s+(.+?)\s*$")


def parse_felt_reports(text: str) -> list[FeltReport]:
    reports = []
    for chunk in re.split(r"[;,]", text or ""):
        match = _FELT_ITEM.match(chunk)
        if match:
            intensity = re.sub(r"\s+", "", match.group(1))
            reports.append(FeltReport(intensity=intensity, place=match.group(2).strip()))
    return reports


def parse_damaging(payload: Any) -> list[DamagingEarthquake]:
    events = []
    for feature in _features(payload):
        props = feature.get("properties") or {}
        try:
            lon, lat = _lon_lat(feature)
            origin = datetime.strptime(
                f"{props.get('date', '').strip()} {props.get('ot_utc', '00:00:00').strip()}",
                "%d-%m-%Y %H:%M:%S",
            ).replace(tzinfo=UTC)
        except (ParseError, ValueError):
            continue
        impact = str(props.get("korban_kerusakan", "")).strip()
        events.append(
            DamagingEarthquake(
                event_id=str(props.get("id_event", "")),
                origin_time=origin,
                magnitude=to_float(props.get("mag")) or 0.0,
                depth_km=to_float(props.get("depth")) or 0.0,
                latitude=lat,
                longitude=lon,
                province=str(props.get("lokasi", "")).strip(),
                epicenter=str(props.get("pusat_gempa", "")).strip(),
                tsunami=str(props.get("tsunami", "")).strip().lower() == "ya",
                impact=impact if impact and impact != "-" else None,
                felt=parse_felt_reports(str(props.get("dirasakan", ""))),
                source=str(props.get("sumber", "")).strip(),
            )
        )
    return sorted(events, key=lambda e: e.origin_time, reverse=True)


def parse_stations(payload: Any, *, network: str) -> list[Station]:
    stations = []
    for feature in _features(payload):
        props = feature.get("properties") or {}
        try:
            lon, lat = _lon_lat(feature)
        except ParseError:
            continue
        if network == "indonesia":
            code, name, net = props.get("id", ""), props.get("stakeholder", ""), "BMKG"
        else:
            code, name, net = (
                props.get("sta", ""),
                props.get("description", ""),
                props.get("net", ""),
            )
        stations.append(
            Station(
                code=str(code).strip(),
                name=str(name).strip(),
                network=str(net).strip(),
                latitude=lat,
                longitude=lon,
            )
        )
    return stations


def parse_faults(payload: Any) -> dict[str, Any]:
    """Strip fault GeoJSON down to line geometries (drops ~40% of the bytes)."""
    features = []
    for feature in _features(payload):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") in {"LineString", "MultiLineString"} and geometry.get(
            "coordinates"
        ):
            features.append({"type": "Feature", "properties": {}, "geometry": geometry})
    return {"type": "FeatureCollection", "features": features}


# ── Tsunami ──────────────────────────────────────────────────


def _bulletin_code(subject: str) -> str:
    match = re.search(r"PD-?\s*([\d.]+)", subject or "", re.IGNORECASE)
    return f"PD-{match.group(1)}" if match else (subject or "").strip()


def _tsunami_media(info: ET.Element, event_id: str, media_url: MediaUrl) -> TsunamiMedia:
    def has(tag: str) -> bool:
        return bool(_text(info, tag))

    return TsunamiMedia(
        shakemap=media_url(event_id, "shakemap") if has("shakemap") else None,
        warning_zones=media_url(event_id, "tsunami-zones") if has("wzmap") else None,
        travel_time=media_url(event_id, "tsunami-travel-time") if has("ttmap") else None,
        sea_height=media_url(event_id, "tsunami-sea-height") if has("sshmap") else None,
    )


def _bulletin(info: ET.Element, media_url: MediaUrl) -> tuple[TsunamiBulletin, dict[str, Any]]:
    event_id = _text(info, "eventid")
    lat, lon = parse_point(_text(info.find("point"), "coordinates"))
    origin = parse_local_datetime(_text(info, "date"), _text(info, "time"))
    if origin is None:
        raise ParseError("tsunami bulletin without origin time")
    zones = [
        WarningZone(
            province=_text(z, "province"),
            district=_text(z, "district"),
            level=_text(z, "level").upper(),
            estimated_arrival=parse_local_datetime(_text(z, "date"), _text(z, "time")),
        )
        for z in info.findall("wzarea")
    ]
    observations = [
        WaveObservation(
            location=_text(o, "location"),
            latitude=to_float(_text(o, "loclatitude")),
            longitude=to_float(_text(o, "loclongitude")),
            height_m=to_float(_text(o, "height")),
            observed_at=parse_local_datetime(_text(o, "date"), _text(o, "time")),
        )
        for o in info.findall("obsarea")
    ]
    bulletin = TsunamiBulletin(
        event_id=event_id,
        code=_bulletin_code(_text(info, "subject")),
        issued_at=parse_sent(_text(info, "timesent")),
        magnitude=_required_float(_text(info, "magnitude"), "magnitude"),
        headline=_text(info, "headline"),
        description=_text(info, "description"),
        warning_zones=zones,
        observations=observations,
        media=_tsunami_media(info, event_id, media_url),
    )
    context = {
        "origin": origin,
        "lat": lat,
        "lon": lon,
        "depth": to_float(_text(info, "depth")) or 0.0,
        "region": _text(info, "area"),
        "instructions": [
            text
            for tag in ("instruction1", "instruction2", "instruction3", "instruction")
            if (text := _text(info, tag))
        ],
    }
    return bulletin, context


def _same_event(a: dict[str, Any], b: dict[str, Any]) -> bool:
    close_in_time = abs((a["origin"] - b["origin"]).total_seconds()) <= 600
    close_in_space = abs(a["lat"] - b["lat"]) <= 2 and abs(a["lon"] - b["lon"]) <= 2
    return close_in_time and close_in_space


def parse_tsunami(xml_text: str | bytes, media_url: MediaUrl) -> list[TsunamiEvent]:
    """Group the flat bulletin list into one TsunamiEvent per earthquake."""
    root = xml_root(xml_text)
    groups: list[list[tuple[TsunamiBulletin, dict[str, Any]]]] = []
    for info in root.findall("info"):
        try:
            item = _bulletin(info, media_url)
        except ParseError:
            continue
        for group in groups:
            if _same_event(group[0][1], item[1]):
                group.append(item)
                break
        else:
            groups.append([item])

    events = []
    for group in groups:
        group.sort(key=lambda it: (it[0].issued_at or it[1]["origin"], it[0].event_id))
        first_ctx = group[0][1]
        latest_bulletin, latest_ctx = group[-1]
        bulletins = [b for b, _ in reversed(group)]
        levels = [z.level for b in bulletins for z in b.warning_zones]
        heights = [o.height_m for b in bulletins for o in b.observations if o.height_m is not None]
        ended = latest_bulletin.code.upper() == "PD-4" or "berakhir" in (
            latest_bulletin.headline.lower()
        )
        events.append(
            TsunamiEvent(
                id=group[0][0].event_id,
                origin_time=latest_ctx["origin"],
                magnitude=latest_bulletin.magnitude,
                depth_km=latest_ctx["depth"],
                latitude=latest_ctx["lat"],
                longitude=latest_ctx["lon"],
                region=latest_ctx["region"] or first_ctx["region"],
                ended=ended,
                max_level=max(levels, key=lambda lv: LEVEL_RANK.get(lv, 0)) if levels else None,
                max_wave_height_m=max(heights) if heights else None,
                bulletins=bulletins,
                instructions=_dedupe(ctx_i for _, c in group for ctx_i in c["instructions"]),
            )
        )
    return sorted(events, key=lambda e: e.origin_time, reverse=True)


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))
