from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

import requests
from requests import Response, Session
from time import time
import xml.etree.ElementTree as ET


class BmkgClientError(Exception):
    """Raised when the BMKG API cannot be reached or returns invalid data."""


@dataclass(slots=True, frozen=True)
class BmkgEndpoints:
    """Endpoint configuration for the BMKG client."""

    alert_url: str
    catalog_url: str
    realtime_url: str
    tsunami_url: str
    felt_url: str


class BmkgClient:
    """Lightweight, typed client for retrieving BMKG earthquake data."""

    def __init__(self, endpoints: BmkgEndpoints, session: Session | None = None, timeout: float = 8.0) -> None:
        self._endpoints = endpoints
        self._session: Session = session or requests.Session()
        self._timeout = timeout
        self._session.headers.setdefault("User-Agent", "ridwaanhall-com/1.0")

    def get_alert(self):
        """Return the most recent felt earthquake alert."""
        return self._get_json(self._endpoints.alert_url)

    def get_catalog(self):
        """Return the catalog of recent earthquakes."""
        return self._get_json(self._endpoints.catalog_url)

    def get_realtime(self):
        """Return realtime earthquakes converted from XML to JSON."""
        xml_text = self._get_text(self._endpoints.realtime_url)
        events = self._parse_realtime_xml(xml_text)
        return {"events": events}

    def get_tsunami(self):
        """Return recent tsunami alerts converted from XML to JSON."""
        xml_text = self._get_text(self._endpoints.tsunami_url)
        return self._parse_tsunami_xml(xml_text)

    def get_felt(self):
        """Return recent felt earthquake alerts converted from XML to JSON."""
        xml_text = self._get_text(self._endpoints.felt_url)
        return self._parse_felt_xml(xml_text)

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

    def _parse_realtime_xml(self, xml_text: str) -> list[dict[str, Any]]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise BmkgClientError("Invalid realtime earthquake data format") from exc

        events: list[dict[str, Any]] = []
        for gempa in root.findall("gempa"):
            events.append(
                {
                    "eventid": (gempa.findtext("eventid") or "").strip(),
                    "status": (gempa.findtext("status") or "").strip(),
                    "datetime": (gempa.findtext("waktu") or "").strip(),
                    "latitude": float(gempa.findtext("lintang") or 0.0),
                    "longitude": float(gempa.findtext("bujur") or 0.0),
                    "depth": int(gempa.findtext("dalam") or 0),
                    "mag": float(gempa.findtext("mag") or 0.0),
                    "fokal": (gempa.findtext("fokal") or "").strip(),
                    "area": (gempa.findtext("area") or "").strip(),
                }
            )

        return events

    def _parse_felt_xml(self, xml_text: str) -> dict[str, Any]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise BmkgClientError("Invalid felt earthquake data format") from exc

        self._strip_namespaces(root)

        def get_text(node: ET.Element | None, tag: str) -> str:
            if node is None:
                return ""
            child = node.find(tag)
            return (child.text or "").strip() if child is not None else ""

        def parse_point(node: ET.Element) -> dict[str, str]:
            point_node = node.find("point")
            return {"coordinates": get_text(point_node, "coordinates")}

        infos: list[dict[str, Any]] = []
        for info in root.findall("info"):
            magnitude_text = get_text(info, "magnitude")
            try:
                magnitude_value = float(magnitude_text) if magnitude_text else None
            except ValueError:
                magnitude_value = None

            infos.append(
                {
                    "event": get_text(info, "event"),
                    "date": get_text(info, "date"),
                    "time": get_text(info, "time"),
                    "point": parse_point(info),
                    "latitude": get_text(info, "latitude"),
                    "longitude": get_text(info, "longitude"),
                    "magnitude": magnitude_value,
                    "depth": get_text(info, "depth"),
                    "area": get_text(info, "area"),
                    "eventid": get_text(info, "eventid"),
                    "potential": get_text(info, "potential"),
                    "subject": get_text(info, "subject"),
                    "headline": get_text(info, "headline"),
                    "description": get_text(info, "description"),
                    "instruction": get_text(info, "instruction"),
                    "shakemap": get_text(info, "shakemap"),
                    "felt": get_text(info, "felt"),
                    "timesent": get_text(info, "timesent"),
                }
            )

        return {
            "identifier": get_text(root, "identifier"),
            "sender": get_text(root, "sender"),
            "sent": get_text(root, "sent"),
            "status": get_text(root, "status"),
            "msgType": get_text(root, "msgType"),
            "scope": get_text(root, "scope"),
            "code": get_text(root, "code"),
            "info": infos,
        }

    def _parse_tsunami_xml(self, xml_text: str) -> dict[str, Any]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise BmkgClientError("Invalid tsunami data format") from exc

        self._strip_namespaces(root)

        def get_text(node: ET.Element | None, tag: str) -> str:
            if node is None:
                return ""
            child = node.find(tag)
            return (child.text or "").strip() if child is not None else ""

        def parse_point(node: ET.Element) -> dict[str, str]:
            point_node = node.find("point")
            return {"coordinates": get_text(point_node, "coordinates")}

        def parse_wzareas(node: ET.Element) -> list[dict[str, str]]:
            areas: list[dict[str, str]] = []
            for area in node.findall("wzarea"):
                areas.append(
                    {
                        "province": get_text(area, "province"),
                        "district": get_text(area, "district"),
                        "level": get_text(area, "level"),
                        "date": get_text(area, "date"),
                        "time": get_text(area, "time"),
                    }
                )
            return areas

        def parse_obsareas(node: ET.Element) -> list[dict[str, str]]:
            areas: list[dict[str, str]] = []
            for area in node.findall("obsarea"):
                areas.append(
                    {
                        "location": get_text(area, "location"),
                        "loclatitude": get_text(area, "loclatitude"),
                        "loclongitude": get_text(area, "loclongitude"),
                        "height": get_text(area, "height"),
                        "date": get_text(area, "date"),
                        "time": get_text(area, "time"),
                    }
                )
            return areas

        infos: list[dict[str, Any]] = []
        for info in root.findall("info"):
            magnitude_text = get_text(info, "magnitude")
            try:
                magnitude_value = float(magnitude_text) if magnitude_text else None
            except ValueError:
                magnitude_value = None

            infos.append(
                {
                    "event": get_text(info, "event"),
                    "date": get_text(info, "date"),
                    "time": get_text(info, "time"),
                    "point": parse_point(info),
                    "latitude": get_text(info, "latitude"),
                    "longitude": get_text(info, "longitude"),
                    "magnitude": magnitude_value,
                    "depth": get_text(info, "depth"),
                    "area": get_text(info, "area"),
                    "eventid": get_text(info, "eventid"),
                    "potential": get_text(info, "potential"),
                    "subject": get_text(info, "subject"),
                    "headline": get_text(info, "headline"),
                    "description": get_text(info, "description"),
                    "instruction": get_text(info, "instruction"),
                    "shakemap": get_text(info, "shakemap"),
                    "wzmap": get_text(info, "wzmap"),
                    "ttmap": get_text(info, "ttmap"),
                    "sshmap": get_text(info, "sshmap"),
                    "instruction1": get_text(info, "instruction1"),
                    "instruction2": get_text(info, "instruction2"),
                    "instruction3": get_text(info, "instruction3"),
                    "timesent": get_text(info, "timesent"),
                    "wzarea": parse_wzareas(info),
                    "obsarea": parse_obsareas(info),
                }
            )

        return {
            "identifier": get_text(root, "identifier"),
            "sender": get_text(root, "sender"),
            "sent": get_text(root, "sent"),
            "status": get_text(root, "status"),
            "msgType": get_text(root, "msgType"),
            "scope": get_text(root, "scope"),
            "code": get_text(root, "code"),
            "info": infos,
        }

    def _strip_namespaces(self, root: ET.Element) -> None:
        """Remove XML namespaces to simplify parsing."""
        for element in root.iter():
            if "}" in element.tag:
                element.tag = element.tag.split("}", 1)[1]

    def _with_cache_buster(self, url: str) -> str:
        """Append a timestamp query param so BMKG responses are not cached."""
        split_url = urlsplit(url)
        query_params = dict(parse_qsl(split_url.query))
        query_params["t"] = str(int(time() * 1000))
        new_query = urlencode(query_params)
        return urlunsplit((split_url.scheme, split_url.netloc, split_url.path, new_query, split_url.fragment))


__all__ = [
    "BmkgClient",
    "BmkgClientError",
    "BmkgEndpoints",
]
