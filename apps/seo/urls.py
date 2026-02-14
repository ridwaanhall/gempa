"""URL configuration for SEO app — robots.txt, sitemap."""

from django.contrib.sitemaps.views import sitemap
from django.urls import path

from .sitemaps import sitemaps
from .views import RobotsTxtView

app_name: str = "seo"

urlpatterns: list = [
    path("robots.txt", RobotsTxtView.as_view(), name="robots-txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]
