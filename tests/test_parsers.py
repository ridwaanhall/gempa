import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.bmkg import parsers
from tests.conftest import fixture_bytes

WIB = timezone(timedelta(hours=7))


def media(event_id: str, kind: str) -> str:
    return f"/m/{event_id}/{kind}"


def test_latest_is_normalised():
    eq = parsers.parse_latest(json.loads(fixture_bytes("datagempa.json")), media)
    assert eq.event_id == "20260926023929"
    assert eq.origin_time == datetime(2026, 9, 26, 2, 39, 29, tzinfo=WIB)
    assert (eq.latitude, eq.longitude) == (-8.23, 120.31)
    assert eq.magnitude == 4.9
    assert eq.depth_km == 9
    assert eq.tsunami_potential is False
    assert eq.media.shakemap == "/m/20260926023929/shakemap"


def test_realtime_sorted_newest_first_in_utc():
    events = parsers.parse_realtime(fixture_bytes("live30event.xml"))
    assert len(events) == 3
    assert events[0].origin_time.tzinfo is UTC
    assert events == sorted(events, key=lambda e: e.origin_time, reverse=True)
    assert all(isinstance(e.magnitude, float) for e in events)


def test_felt_list_parses_cap_xml():
    events = parsers.parse_alert_list(fixture_bytes("last30feltevent.xml"), media)
    assert len(events) == 2
    assert events[0].felt


def test_tsunami_bulletins_grouped_per_earthquake():
    events = parsers.parse_tsunami(fixture_bytes("last30tsunamievent.xml"), media)
    assert len(events) == 2
    first = events[0]
    assert first.bulletins[0].code == "PD-4"
    assert first.ended is True
    assert first.max_level in {"AWAS", "SIAGA", "WASPADA"}
    assert first.max_wave_height_m and first.max_wave_height_m > 0
    assert first.bulletins == sorted(first.bulletins, key=lambda b: b.issued_at, reverse=True)


def test_damaging_catalogue():
    events = parsers.parse_damaging(json.loads(fixture_bytes("katalog_gempa.json")))
    assert len(events) == 3
    assert events[0].origin_time.tzinfo is UTC
    assert all(isinstance(e.tsunami, bool) for e in events)
    assert events[0].felt and events[0].felt[0].intensity


def test_archive_and_stations_and_faults():
    archive = parsers.parse_archive(json.loads(fixture_bytes("3mgempaQL.json")))
    assert archive[0].magnitude == round(archive[0].magnitude, 1)
    indo = parsers.parse_stations(
        json.loads(fixture_bytes("sensor_seismic.json")), network="indonesia"
    )
    world = parsers.parse_stations(
        json.loads(fixture_bytes("sensor_global.json")), network="global"
    )
    assert indo[0].network == "BMKG" and world[0].network
    faults = parsers.parse_faults(json.loads(fixture_bytes("indo_faults_lines.geojson")))
    assert faults["features"][0]["properties"] == {}


def test_history_text():
    text = (
        "# Timestamp(UTC), +OT, Lat, Lon, Depth, Phase, MagType, Mag, MagCount, Status\n"
        "2026-09-26 08:12:08|    1.76|  -8.16| 120.23|     10|   15|         MLv| 3.31|    4|M\n"
        "garbage line\n"
    )
    history = parsers.parse_history("bmg2026swgz", text)
    assert len(history.records) == 1
    assert history.records[0].magnitude == 3.31


@pytest.mark.parametrize(
    ("text", "expected"),
    [("8.23 LS", -8.23), ("4.74 LU", 4.74), ("120.31 BT", 120.31), ("10.5 BB", -10.5), ("", None)],
)
def test_signed_coordinate(text, expected):
    assert parsers.signed_coordinate(text) == expected


@pytest.mark.parametrize(
    ("date", "time", "hour_offset"),
    [
        ("26-09-26", "02:39:29 WIB", 7),
        ("15-08-2026", "05:02 WITA", 8),
        ("01-01-26", "00:00:00 WIT", 9),
    ],
)
def test_local_datetime_zones(date, time, hour_offset):
    parsed = parsers.parse_local_datetime(date, time)
    assert parsed is not None
    assert parsed.utcoffset() == timedelta(hours=hour_offset)


def test_felt_reports():
    reports = parsers.parse_felt_reports("IV Padang;III - IV Siberut, II Nias")
    assert [(r.intensity, r.place) for r in reports] == [
        ("IV", "Padang"),
        ("III-IV", "Siberut"),
        ("II", "Nias"),
    ]


def test_invalid_xml_raises():
    with pytest.raises(parsers.ParseError):
        parsers.parse_realtime(b"<not-xml")
