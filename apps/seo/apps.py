from django.apps import AppConfig


class SeoConfig(AppConfig):
    """SEO app — meta tags, sitemap, robots.txt, structured data, security headers."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.seo'
    verbose_name = 'SEO'
