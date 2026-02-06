from django.urls import path

from . import views
    
urlpatterns = [
	path("latest/", views.EarthquakeAlertView.as_view(), name="earthquake-latest"),
	path("catalog/", views.EarthquakeCatalogView.as_view(), name="earthquake-catalog"),
	path("realtime/", views.EarthquakeRealtimeView.as_view(), name="earthquake-realtime"),
	path("tsunami/", views.TsunamiAlertView.as_view(), name="earthquake-tsunami"),
	path("felt/", views.FeltAlertView.as_view(), name="earthquake-felt"),
	path("m5/", views.M5AlertView.as_view(), name="earthquake-m5"),
	path("mon3/", views.Mon3View.as_view(), name="earthquake-mon3"),
	path("yr5/", views.Yr5View.as_view(), name="earthquake-yr5"),
	path("seismic/", views.SeismicView.as_view(), name="earthquake-seismic"),
	path("global/", views.GlobalSensorView.as_view(), name="earthquake-global"),
]