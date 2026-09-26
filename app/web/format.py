"""Jinja filters mirroring `static/js/lib/format.js`, so server-rendered HTML
matches what the client renders on hydration. All times are shown in WIB."""

from datetime import UTC, datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
EMPTY = "–"  # noqa: RUF001 — en dash placeholder, same as the client
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
_MONTHS_LONG = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]  # fmt: skip
_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_CATEGORY = {0: "Mikro", 3: "Minor", 4: "Ringan", 5: "Sedang", 6: "Kuat", 7: "Besar"}


def _dt(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.astimezone(WIB)


def decimal(value: float | None, digits: int = 1) -> str:
    return EMPTY if value is None else f"{value:.{digits}f}".replace(".", ",")


def mag(value: float | None) -> str:
    return decimal(value, 1)


def mag_bucket(value: float | None) -> int:
    if value is None or value < 3:
        return 0
    return min(7, int(value))


def mag_category(value: float | None) -> str:
    return _CATEGORY[mag_bucket(value)]


def depth(km: float | None) -> str:
    return EMPTY if km is None else f"{round(km):,} km".replace(",", ".")


def coords(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return EMPTY
    ns = "LS" if lat < 0 else "LU"
    ew = "BB" if lon < 0 else "BT"
    return f"{decimal(abs(lat), 2)}° {ns}, {decimal(abs(lon), 2)}° {ew}"


def wib(value: datetime | str) -> str:
    """`26 Sep 2026, 02.39 WIB`"""
    d = _dt(value)
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}, {d:%H.%M} WIB"


def wib_long(value: datetime | str) -> str:
    """`Sabtu, 26 September 2026 pukul 02.39.29 WIB`"""
    d = _dt(value)
    return (
        f"{_DAYS[d.weekday()]}, {d.day} {_MONTHS_LONG[d.month - 1]} {d.year} pukul {d:%H.%M.%S} WIB"
    )


def utc_date(value: datetime | str) -> str:
    """`13 Mar 2022` (catalogue dates are UTC)."""
    d = _dt(value).astimezone(UTC)
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}"


def iso(value: datetime | str) -> str:
    return _dt(value).isoformat()


FILTERS = {
    "mag": mag,
    "mag_bucket": mag_bucket,
    "mag_category": mag_category,
    "depth": depth,
    "wib": wib,
    "wib_long": wib_long,
    "iso": iso,
    "utc_date": utc_date,
    "decimal": decimal,
}

GLOBALS = {"coords": coords}
