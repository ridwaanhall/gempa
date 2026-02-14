"""BMKG earthquake data client — OOP design with full type annotations.

This module lives in ``apps.core`` so both the REST API layer
(``apps.api``) and the web front-end (``apps.web``) can reuse
the same networking / parsing logic without duplication.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from time import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests import Response, Session


# ── Exceptions ───────────────────────────────────────────────


class BmkgClientError(Exception):
    """Raised when the BMKG API cannot be reached or returns invalid data."""


# ── Configuration ────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class BmkgEndpoints:
    """Immutable endpoint configuration for the BMKG earthquake client."""

    alert_url: str
    catalog_url: str
    realtime_url: str
    tsunami_url: str
    felt_url: str
    m5_url: str
    mon3_url: str
    yr5_url: str
    seismic_url: str
    global_url: str
    faults_global_url: str
    faults_indo_url: str
    history_url_template: str


# ── XML / text parsing helpers ───────────────────────────────


class XmlHelper:
    """Stateless utility providing common XML parsing operations."""

    @staticmethod
    def parse_root(xml_text: str, error_msg: str) -> ET.Element:
        """Parse *xml_text* into an :class:`ET.Element`, stripping namespaces."""
        try:
            root: ET.Element = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise BmkgClientError(error_msg) from exc
        XmlHelper._strip_namespaces(root)
        return root

    @staticmethod
    def get_text(node: ET.Element | None, tag: str) -> str:
        """Return stripped text of *tag* child, or ``""``."""
        if node is None:
            return ""
        child: ET.Element | None = node.find(tag)
        return (child.text or "").strip() if child is not None else ""

    @staticmethod
    def parse_point(node: ET.Element) -> dict[str, str]:
        """Extract ``<point><coordinates>`` from *node*."""
        point_node: ET.Element | None = node.find("point")
        return {"coordinates": XmlHelper.get_text(point_node, "coordinates")}

    @staticmethod
    def parse_magnitude(text: str) -> float | None:
        """Try to parse a magnitude string; return ``None`` on failure."""
        try:
            return float(text) if text else None
        except ValueError:
            return None

    @staticmethod
    def parse_envelope(root: ET.Element) -> dict[str, str]:
        """Extract standard CAP alert envelope fields."""
        gt = XmlHelper.get_text
        return {
            "identifier": gt(root, "identifier"),
            "sender": gt(root, "sender"),
            "sent": gt(root, "sent"),
            "status": gt(root, "status"),
            "msgType": gt(root, "msgType"),
            "scope": gt(root, "scope"),
            "code": gt(root, "code"),
        }

    @staticmethod
    def parse_base_info(info: ET.Element) -> dict[str, Any]:
        """Extract fields common to every alert ``<info>`` block."""
        gt = XmlHelper.get_text
        return {
            "event": gt(info, "event"),
            "date": gt(info, "date"),
            "time": gt(info, "time"),
            "point": XmlHelper.parse_point(info),
            "latitude": gt(info, "latitude"),
            "longitude": gt(info, "longitude"),
            "magnitude": XmlHelper.parse_magnitude(gt(info, "magnitude")),
            "depth": gt(info, "depth"),
            "area": gt(info, "area"),
            "eventid": gt(info, "eventid"),
            "potential": gt(info, "potential"),
            "subject": gt(info, "subject"),
            "headline": gt(info, "headline"),
            "description": gt(info, "description"),
            "instruction": gt(info, "instruction"),
            "shakemap": gt(info, "shakemap"),
            "timesent": gt(info, "timesent"),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _strip_namespaces(root: ET.Element) -> None:
        for element in root.iter():
            if "}" in element.tag:
                element.tag = element.tag.split("}", 1)[1]


class ValueParser:
    """Safe primitive-value converters used by the history parser."""

    @staticmethod
    def to_float(value: str) -> float | None:
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def to_int(value: str) -> int | None:
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None


# ── Main client ──────────────────────────────────────────────


class BmkgClient:
    """Typed HTTP client for retrieving and parsing BMKG earthquake data.

    Provides methods to fetch earthquake alerts, real-time events, tsunami
    warnings, historical data, and sensor information from the BMKG
    (Indonesian Meteorological, Climatological, and Geophysical Agency) APIs.
    """

    def __init__(
        self,
        endpoints: BmkgEndpoints,
        session: Session | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._endpoints: BmkgEndpoints = endpoints
        self._session: Session = session or requests.Session()
        self._timeout: float = timeout
        self._session.headers.setdefault("User-Agent", "ridwaanhall-com/1.0")

    # ── Public API ───────────────────────────────────────────

    def get_alert(self) -> dict[str, Any]:
        """Latest felt earthquake alert (JSON)."""
        return self._fetch_json(self._endpoints.alert_url)

    def get_damage(self) -> dict[str, Any]:
        """Historical damaging earthquakes catalog (GeoJSON)."""
        return self._fetch_json(self._endpoints.catalog_url)

    def get_realtime(self) -> dict[str, Any]:
        """Real-time earthquake events (XML → dict)."""
        xml_text: str = self._fetch_text(self._endpoints.realtime_url)
        events: list[dict[str, Any]] = self._parse_realtime_xml(xml_text)
        return {"events": events}

    def get_tsunami(self) -> dict[str, Any]:
        """Recent tsunami alerts (XML → dict)."""
        xml_text: str = self._fetch_text(self._endpoints.tsunami_url)
        return self._parse_tsunami_xml(xml_text)

    def get_felt(self) -> dict[str, Any]:
        """Recent felt earthquake alerts (XML → dict)."""
        xml_text: str = self._fetch_text(self._endpoints.felt_url)
        return self._parse_felt_xml(xml_text)

    def get_m5(self) -> dict[str, Any]:
        """Recent M5+ earthquake alerts (XML → dict)."""
        xml_text: str = self._fetch_text(self._endpoints.m5_url)
        return self._parse_m5_xml(xml_text)

    def get_mon3(self) -> dict[str, Any]:
        """3-month M3+ earthquake monitoring feed (GeoJSON)."""
        return self._fetch_json(self._endpoints.mon3_url)

    def get_yr5(self) -> dict[str, Any]:
        """5-year historical earthquake data (GeoJSON)."""
        return self._fetch_json(self._endpoints.yr5_url)

    def get_seismic(self) -> dict[str, Any]:
        """Indonesian seismic sensor stations (GeoJSON)."""
        return self._fetch_json(self._endpoints.seismic_url)

    def get_global(self) -> dict[str, Any]:
        """Global seismic sensor stations."""
        data: Any = self._fetch_json_any(self._endpoints.global_url)
        if isinstance(data, list):
            return {"features": data}
        raise BmkgClientError("Invalid global sensor data format")

    def get_faults_global(self) -> dict[str, Any]:
        """Global fault lines (GeoJSON)."""
        return self._fetch_json(self._endpoints.faults_global_url)

    def get_faults_indo(self) -> dict[str, Any]:
        """Indonesian fault lines (GeoJSON)."""
        return self._fetch_json(self._endpoints.faults_indo_url)

    def get_history(self, eventid: str) -> dict[str, Any]:
        """Update-history of a real-time event by its ID."""
        url: str = self._endpoints.history_url_template.format(eventid=eventid)
        text: str = self._fetch_text(url)
        records: list[dict[str, Any]] = self._parse_history_text(text)
        return {"eventid": eventid, "records": records}

    # ── HTTP helpers ─────────────────────────────────────────

    def _fetch(self, url: str) -> Response:
        """Perform a GET request with cache-busting."""
        cache_busted_url: str = self._cache_bust(url)
        try:
            response: Response = self._session.get(
                cache_busted_url, timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise BmkgClientError("Failed to fetch earthquake data") from exc
        return response

    def _fetch_json(self, url: str) -> dict[str, Any]:
        response: Response = self._fetch(url)
        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            raise BmkgClientError("Invalid earthquake data format") from exc
        return data

    def _fetch_json_any(self, url: str) -> Any:
        response: Response = self._fetch(url)
        try:
            return response.json()
        except ValueError as exc:
            raise BmkgClientError("Invalid earthquake data format") from exc

    def _fetch_text(self, url: str) -> str:
        return self._fetch(url).text

    # ── XML parsers ──────────────────────────────────────────

    def _parse_realtime_xml(self, xml_text: str) -> list[dict[str, Any]]:
        root: ET.Element = XmlHelper.parse_root(
            xml_text, "Invalid realtime earthquake data format",
        )
        gt = XmlHelper.get_text
        events: list[dict[str, Any]] = []
        for gempa in root.findall("gempa"):
            events.append({
                "eventid": gt(gempa, "eventid"),
                "status": gt(gempa, "status"),
                "datetime": gt(gempa, "waktu"),
                "latitude": float(gt(gempa, "lintang") or "0"),
                "longitude": float(gt(gempa, "bujur") or "0"),
                "depth": int(gt(gempa, "dalam") or "0"),
                "mag": float(gt(gempa, "mag") or "0"),
                "fokal": gt(gempa, "fokal"),
                "area": gt(gempa, "area"),
            })
        return events

    def _parse_m5_xml(self, xml_text: str) -> dict[str, Any]:
        root: ET.Element = XmlHelper.parse_root(xml_text, "Invalid M5 data format")
        infos: list[dict[str, Any]] = [
            XmlHelper.parse_base_info(info) for info in root.findall("info")
        ]
        envelope: dict[str, Any] = XmlHelper.parse_envelope(root)
        envelope["info"] = infos
        return envelope

    def _parse_felt_xml(self, xml_text: str) -> dict[str, Any]:
        root: ET.Element = XmlHelper.parse_root(
            xml_text, "Invalid felt earthquake data format",
        )
        infos: list[dict[str, Any]] = []
        for info in root.findall("info"):
            entry: dict[str, Any] = XmlHelper.parse_base_info(info)
            entry["felt"] = XmlHelper.get_text(info, "felt")
            infos.append(entry)
        envelope: dict[str, Any] = XmlHelper.parse_envelope(root)
        envelope["info"] = infos
        return envelope

    def _parse_tsunami_xml(self, xml_text: str) -> dict[str, Any]:
        root: ET.Element = XmlHelper.parse_root(
            xml_text, "Invalid tsunami data format",
        )
        gt = XmlHelper.get_text
        infos: list[dict[str, Any]] = []
        for info in root.findall("info"):
            entry: dict[str, Any] = XmlHelper.parse_base_info(info)
            entry.update({
                "wzmap": gt(info, "wzmap"),
                "ttmap": gt(info, "ttmap"),
                "sshmap": gt(info, "sshmap"),
                "instruction1": gt(info, "instruction1"),
                "instruction2": gt(info, "instruction2"),
                "instruction3": gt(info, "instruction3"),
                "wzarea": self._parse_wz_areas(info),
                "obsarea": self._parse_obs_areas(info),
            })
            infos.append(entry)
        envelope: dict[str, Any] = XmlHelper.parse_envelope(root)
        envelope["info"] = infos
        return envelope

    @staticmethod
    def _parse_wz_areas(node: ET.Element) -> list[dict[str, str]]:
        gt = XmlHelper.get_text
        return [
            {
                "province": gt(area, "province"),
                "district": gt(area, "district"),
                "level": gt(area, "level"),
                "date": gt(area, "date"),
                "time": gt(area, "time"),
            }
            for area in node.findall("wzarea")
        ]

    @staticmethod
    def _parse_obs_areas(node: ET.Element) -> list[dict[str, str]]:
        gt = XmlHelper.get_text
        return [
            {
                "location": gt(area, "location"),
                "loclatitude": gt(area, "loclatitude"),
                "loclongitude": gt(area, "loclongitude"),
                "height": gt(area, "height"),
                "date": gt(area, "date"),
                "time": gt(area, "time"),
            }
            for area in node.findall("obsarea")
        ]

    # ── History parser ───────────────────────────────────────

    @staticmethod
    def _parse_history_text(text: str) -> list[dict[str, Any]]:
        vp = ValueParser
        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            stripped: str = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts: list[str] = [p.strip() for p in stripped.split("|")]
            if len(parts) < 10:
                continue
            (
                timestamp, ot_minutes, lat, lon, depth,
                phase_count, mag_type, magnitude, mag_count, rec_status,
            ) = parts[:10]
            records.append({
                "timestamp": timestamp,
                "ot_minutes": vp.to_float(ot_minutes),
                "latitude": vp.to_float(lat),
                "longitude": vp.to_float(lon),
                "depth": vp.to_float(depth),
                "phase_count": vp.to_int(phase_count),
                "mag_type": mag_type,
                "magnitude": vp.to_float(magnitude),
                "mag_count": vp.to_int(mag_count),
                "status": rec_status,
            })
        return records

    # ── Utilities ────────────────────────────────────────────

    @staticmethod
    def _cache_bust(url: str) -> str:
        split = urlsplit(url)
        params: dict[str, str] = dict(parse_qsl(split.query))
        params["t"] = str(int(time() * 1000))
        return urlunsplit((
            split.scheme, split.netloc, split.path,
            urlencode(params), split.fragment,
        ))


__all__: list[str] = [
    "BmkgClient",
    "BmkgClientError",
    "BmkgEndpoints",
    "XmlHelper",
    "ValueParser",
]
