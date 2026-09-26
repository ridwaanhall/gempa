"""Public API contract.

BMKG publishes a dozen feeds in mixed formats (CAP XML, GeoJSON with string
numbers, pipe-delimited text) with Indonesian keys and a mix of WIB and UTC
times. Everything the API returns is normalised into these models:

* English snake_case keys.
* Numbers are numbers; coordinates are signed decimal degrees (WGS84).
* Datetimes are ISO 8601 with an explicit offset.
* Media are referenced by our own `/api/v1/media/...` URLs, never upstream ones.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(frozen=True)


# ── Envelope ─────────────────────────────────────────────────


class Meta(Schema):
    count: int = Field(description="Number of items in `data`.")
    source: str = Field(default="BMKG", description="Upstream data provider.")
    generated_at: datetime = Field(description="When this payload was built (UTC).")


class Envelope[T](Schema):
    data: T
    meta: Meta


# ── Earthquakes ──────────────────────────────────────────────


class EventMedia(Schema):
    shakemap: str | None = Field(default=None, description="Shaking-intensity (MMI) map image.")
    location_map: str | None = Field(default=None, description="Accelerometer distribution map.")
    station_intensity: str | None = Field(default=None, description="Station PGA and MMI table.")
    impact: str | None = Field(default=None, description="Estimated impact by district.")
    intensity: str | None = Field(default=None, description="Intensity summary graphic.")


class Earthquake(Schema):
    """An earthquake announced by BMKG (latest, felt, or M5+ feeds). Times are WIB."""

    event_id: str = Field(examples=["20260926023929"])
    origin_time: datetime = Field(description="Origin time, WIB (+07:00).")
    magnitude: float
    depth_km: float
    latitude: float
    longitude: float
    region: str = Field(description="Human-readable location of the epicentre.")
    tsunami_potential: bool = Field(description="True if BMKG flags tsunami potential.")
    potential: str = Field(description="BMKG's potential statement, verbatim.")
    felt: str | None = Field(
        default=None, description="MMI felt reports, e.g. 'III Sumur, II Anyer'."
    )
    instruction: str | None = None
    has_narrative: bool = Field(
        default=False, description="Whether a BMKG press narrative is likely available."
    )
    media: EventMedia


class RealtimeEvent(Schema):
    """Automatic real-time detection from the BMKG seismic network. Times are UTC."""

    event_id: str = Field(examples=["bmg2026swgz"])
    origin_time: datetime
    magnitude: float
    depth_km: float
    latitude: float
    longitude: float
    region: str
    status: str = Field(description="Processing status, e.g. 'confirmed'.")
    has_focal_mechanism: bool


class HistoryRecord(Schema):
    """One revision of a real-time solution."""

    timestamp: datetime = Field(description="When the revision was computed (UTC).")
    minutes_after_origin: float | None
    latitude: float | None
    longitude: float | None
    depth_km: float | None
    phase_count: int | None
    magnitude_type: str | None
    magnitude: float | None
    magnitude_count: int | None
    status: str | None


class EventHistory(Schema):
    event_id: str
    records: list[HistoryRecord]


class ArchiveEvent(Schema):
    """Event from the reviewed catalogue (3-month M4.5+ or 5-year M5+). Times are UTC."""

    event_id: str
    origin_time: datetime
    magnitude: float
    depth_km: float
    latitude: float
    longitude: float
    region: str
    phase_count: int | None
    status: str


class ArchivePeriod(StrEnum):
    three_months = "3m"
    five_years = "5y"


class FeltReport(Schema):
    intensity: str = Field(description="MMI scale value, e.g. 'IV' or 'II-III'.")
    place: str


class DamagingEarthquake(Schema):
    """Historical earthquake that caused damage or casualties."""

    event_id: str
    origin_time: datetime = Field(description="UTC.")
    magnitude: float
    depth_km: float
    latitude: float
    longitude: float
    province: str
    epicenter: str
    tsunami: bool
    impact: str | None = Field(description="Casualties and damage, verbatim (Indonesian).")
    felt: list[FeltReport]
    source: str


# ── Tsunami ──────────────────────────────────────────────────


class WarningZone(Schema):
    province: str
    district: str
    level: str = Field(description="AWAS (highest), SIAGA, or WASPADA.")
    estimated_arrival: datetime | None = Field(description="Estimated arrival time, WIB.")


class WaveObservation(Schema):
    location: str
    latitude: float | None
    longitude: float | None
    height_m: float | None
    observed_at: datetime | None


class TsunamiMedia(Schema):
    shakemap: str | None = None
    warning_zones: str | None = None
    travel_time: str | None = None
    sea_height: str | None = None


class TsunamiBulletin(Schema):
    event_id: str
    code: str = Field(description="Bulletin sequence, e.g. 'PD-1', 'PD-3.2', 'PD-4' (ended).")
    issued_at: datetime | None
    magnitude: float
    headline: str
    description: str
    warning_zones: list[WarningZone]
    observations: list[WaveObservation]
    media: TsunamiMedia


class TsunamiEvent(Schema):
    """All warning bulletins BMKG issued for one earthquake, newest first."""

    id: str = Field(description="Event id of the first bulletin.")
    origin_time: datetime
    magnitude: float = Field(description="Latest revised magnitude.")
    depth_km: float
    latitude: float
    longitude: float
    region: str
    ended: bool = Field(description="True once BMKG has declared the warning over.")
    max_level: str | None = Field(description="Highest warning level issued.")
    max_wave_height_m: float | None
    bulletins: list[TsunamiBulletin]
    instructions: list[str]


# ── Stations & faults ────────────────────────────────────────


class StationNetwork(StrEnum):
    indonesia = "indonesia"
    global_ = "global"


class Station(Schema):
    code: str
    name: str
    network: str
    latitude: float
    longitude: float


class FaultScope(StrEnum):
    indonesia = "indonesia"
    global_ = "global"


# ── Misc ─────────────────────────────────────────────────────


class Narrative(Schema):
    event_id: str
    html: str = Field(description="BMKG press narrative, sanitised HTML (Indonesian).")


class Health(Schema):
    status: Literal["ok"]
    version: str


class Problem(Schema):
    detail: str


__all__ = [
    "ArchiveEvent",
    "ArchivePeriod",
    "DamagingEarthquake",
    "Earthquake",
    "Envelope",
    "EventHistory",
    "EventMedia",
    "FaultScope",
    "FeltReport",
    "Health",
    "HistoryRecord",
    "Meta",
    "Narrative",
    "Problem",
    "RealtimeEvent",
    "Station",
    "StationNetwork",
    "TsunamiBulletin",
    "TsunamiEvent",
    "TsunamiMedia",
    "WarningZone",
    "WaveObservation",
]
