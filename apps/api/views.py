from __future__ import annotations

from typing import Any, Callable

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from . import serializers
from .services import bmkg_client


class ValidatedRemoteView(APIView):
	"""Base view that fetches remote data and returns validated payload."""

	serializer_class: type[Serializer]
	fetcher: Callable[[], Any]
	http_method_names = ["get"]

	def get(self, request, *args, **kwargs) -> Response:  # type: ignore[override]
		try:
			payload: dict[str, Any] = self.fetcher()
		except bmkg_client.BmkgClientError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

		serializer = self.serializer_class(data=payload)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.data)


_bmkg_endpoints = bmkg_client.BmkgEndpoints(
	alert_url=settings.BMKG_ALERT_URL,
	catalog_url=settings.BMKG_CATALOG_URL,
	realtime_url=settings.BMKG_REALTIME_URL,
	tsunami_url=settings.BMKG_TSUNAMI_URL,
	felt_url=settings.BMKG_FELT_URL,
	m5_url=settings.BMKG_M5_URL,
	mon3_url=settings.BMKG_MON3_URL,
	yr5_url=settings.BMKG_YR5_URL,
	seismic_url=settings.BMKG_SEISMIC_URL,
	global_url=settings.BMKG_GLOBAL_URL,
	faults_global_url=settings.BMKG_FAULTS_GLOBAL_URL,
	faults_indo_url=settings.BMKG_FAULTS_INDO_URL,
)
_client = bmkg_client.BmkgClient(endpoints=_bmkg_endpoints)


class EarthquakeAlertView(ValidatedRemoteView):
	"""Expose the latest felt earthquake alert from BMKG."""

	serializer_class = serializers.EarthquakeAlertSerializer
	fetcher = _client.get_alert


class EarthquakeCatalogView(ValidatedRemoteView):
	"""Expose the earthquake catalog from BMKG."""

	serializer_class = serializers.CatalogSerializer
	fetcher = _client.get_catalog


class EarthquakeRealtimeView(ValidatedRemoteView):
	"""Expose realtime earthquakes parsed from BMKG XML feed."""

	serializer_class = serializers.RealtimeCatalogSerializer
	fetcher = _client.get_realtime


class TsunamiAlertView(ValidatedRemoteView):
	"""Expose recent tsunami alerts parsed from BMKG XML feed."""

	serializer_class = serializers.TsunamiAlertSerializer
	fetcher = _client.get_tsunami


class FeltAlertView(ValidatedRemoteView):
	"""Expose recent felt earthquake alerts parsed from BMKG XML feed."""

	serializer_class = serializers.FeltAlertSerializer
	fetcher = _client.get_felt


class M5AlertView(ValidatedRemoteView):
	"""Expose recent M5+ earthquake alerts parsed from BMKG XML feed."""

	serializer_class = serializers.M5AlertSerializer
	fetcher = _client.get_m5


class Mon3View(ValidatedRemoteView):
	"""Expose monitoring feed for M3+ earthquakes (GeoJSON)."""

	serializer_class = serializers.Mon3CatalogSerializer
	fetcher = _client.get_mon3


class Yr5View(ValidatedRemoteView):
	"""Expose 5-year historical earthquakes (GeoJSON)."""

	serializer_class = serializers.Yr5CatalogSerializer
	fetcher = _client.get_yr5


class SeismicView(ValidatedRemoteView):
	"""Expose seismic sensor stations (GeoJSON FeatureCollection)."""

	serializer_class = serializers.SeismicCatalogSerializer
	fetcher = _client.get_seismic


class GlobalSensorView(ValidatedRemoteView):
	"""Expose global sensor stations (Feature list)."""

	serializer_class = serializers.GlobalCatalogSerializer
	fetcher = _client.get_global


class FaultsGlobalView(ValidatedRemoteView):
	"""Expose global/Indo faults GeoJSON."""

	serializer_class = serializers.FaultCatalogSerializer
	fetcher = _client.get_faults_global


class FaultsIndoView(ValidatedRemoteView):
	"""Expose Indonesian faults GeoJSON."""

	serializer_class = serializers.FaultCatalogSerializer
	fetcher = _client.get_faults_indo
