"""URL configuration for the web front-end."""

from django.urls import path

from . import views

app_name: str = "web"

urlpatterns: list = [
    path("", views.SingleRealtimeView.as_view(), name="single_realtime"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("realtime/", views.RealtimeView.as_view(), name="realtime"),
    path("felt/", views.FeltView.as_view(), name="felt"),
    path("tsunami/", views.TsunamiView.as_view(), name="tsunami"),
    path("m5/", views.M5View.as_view(), name="m5"),
    path("damage/", views.DamageView.as_view(), name="damage"),
]
