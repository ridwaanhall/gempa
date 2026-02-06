from django.urls import path

from apps.api.views import EarthquakeAlertView, EarthquakeCatalogView

urlpatterns = [
	path("alerts/latest/", EarthquakeAlertView.as_view(), name="earthquake-alert-latest"),
	path("catalog/", EarthquakeCatalogView.as_view(), name="earthquake-catalog"),
]