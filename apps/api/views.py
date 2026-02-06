from __future__ import annotations

from typing import Any, Callable

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from apps.api.serializers import CatalogSerializer, EarthquakeAlertSerializer, RealtimeCatalogSerializer
from apps.api.services.bmkg_client import BmkgClient, BmkgClientError, BmkgEndpoints


class ValidatedRemoteView(APIView):
	"""Base view that fetches remote data and returns validated payload."""

	serializer_class: type[Serializer]
	fetcher: Callable[[], Any]
	http_method_names = ["get"]

	def get(self, request, *args, **kwargs) -> Response:  # type: ignore[override]
		try:
			payload: dict[str, Any] = self.fetcher()
		except BmkgClientError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

		serializer = self.serializer_class(data=payload)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.data)


_bmkg_endpoints = BmkgEndpoints(
	alert_url=settings.BMKG_ALERT_URL,
	catalog_url=settings.BMKG_CATALOG_URL,
	realtime_url=settings.BMKG_REALTIME_URL,
)
_client = BmkgClient(endpoints=_bmkg_endpoints)


class EarthquakeAlertView(ValidatedRemoteView):
	"""Expose the latest felt earthquake alert from BMKG."""

	serializer_class = EarthquakeAlertSerializer
	fetcher = _client.get_alert


class EarthquakeCatalogView(ValidatedRemoteView):
	"""Expose the earthquake catalog from BMKG."""

	serializer_class = CatalogSerializer
	fetcher = _client.get_catalog


class EarthquakeRealtimeView(ValidatedRemoteView):
	"""Expose realtime earthquakes parsed from BMKG XML feed."""

	serializer_class = RealtimeCatalogSerializer
	fetcher = _client.get_realtime
