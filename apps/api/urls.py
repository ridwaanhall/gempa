from django.urls import path

from apps.api.views import EarthquakeAlertView, EarthquakeCatalogView, EarthquakeRealtimeView

urlpatterns = [
	path("latest/", EarthquakeAlertView.as_view(), name="earthquake-latest"),
	path("catalog/", EarthquakeCatalogView.as_view(), name="earthquake-catalog"),
	path("realtime/", EarthquakeRealtimeView.as_view(), name="earthquake-realtime"),
]