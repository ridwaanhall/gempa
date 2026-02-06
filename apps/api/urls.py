from django.urls import path

from . import views
    
urlpatterns = [
    # realtime
	path("realtime/", views.EarthquakeRealtimeView.as_view(), name="earthquake-realtime"),
	path("realtime/<str:eventid>/history/", views.EarthquakeHistoryView.as_view(), name="earthquake-history"),

    # alerts
	path("latest/", views.EarthquakeAlertView.as_view(), name="earthquake-latest"),
	path("damage/", views.EarthquakeDamageView.as_view(), name="earthquake-damage"),
	path("tsunami/", views.TsunamiAlertView.as_view(), name="earthquake-tsunami"),
	path("felt/", views.FeltAlertView.as_view(), name="earthquake-felt"),
	path("m5/", views.M5AlertView.as_view(), name="earthquake-m5"),
 
    # historical
	path("mon3/", views.Mon3View.as_view(), name="earthquake-mon3"),
	path("yr5/", views.Yr5View.as_view(), name="earthquake-yr5"),
 
    # seismic
	path("seismic-indo/", views.SeismicView.as_view(), name="seismic-indo"),
	path("seismic-global/", views.GlobalSensorView.as_view(), name="seismic-global"),
 
    # faults
	path("faults-indo/", views.FaultsIndoView.as_view(), name="faults-indo"),
	path("faults-global/", views.FaultsGlobalView.as_view(), name="faults-global"),
]