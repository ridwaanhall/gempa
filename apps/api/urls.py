from django.urls import path

from . import views
    
urlpatterns = [
	path("latest/", views.EarthquakeAlertView.as_view(), name="earthquake-latest"),
	path("catalog/", views.EarthquakeCatalogView.as_view(), name="earthquake-catalog"),
	path("realtime/", views.EarthquakeRealtimeView.as_view(), name="earthquake-realtime"),
	path("tsunami/", views.TsunamiAlertView.as_view(), name="earthquake-tsunami"),
]