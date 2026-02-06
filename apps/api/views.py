from __future__ import annotations

from typing import Any, Callable

from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from apps.api.serializers import CatalogSerializer, EarthquakeAlertSerializer
from apps.api.services.bmkg_client import BmkgClient, BmkgClientError


class ValidatedRemoteView(APIView):
	"""Base view that fetches remote data and returns validated payload."""

	serializer_class: type[Serializer]
	fetcher: Callable[[], dict[str, Any]]
	http_method_names = ["get"]

	def get(self, request, *args, **kwargs) -> Response:  # type: ignore[override]
		try:
			payload: dict[str, Any] = self.fetcher()
		except BmkgClientError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

		serializer = self.serializer_class(data=payload)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.data)


_client = BmkgClient()


class EarthquakeAlertView(ValidatedRemoteView):
	"""Expose the latest felt earthquake alert from BMKG."""

	serializer_class = EarthquakeAlertSerializer
	fetcher = _client.get_alert


class EarthquakeCatalogView(ValidatedRemoteView):
	"""Expose the earthquake catalog from BMKG."""

	serializer_class = CatalogSerializer
	fetcher = _client.get_catalog
