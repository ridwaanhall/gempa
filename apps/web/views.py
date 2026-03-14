"""Web front-end views — render HTML shells; JS fetches data from /api/."""

from __future__ import annotations

from typing import Any

from django.views.generic import TemplateView


class BasePageView(TemplateView):
    """Base view that injects common context (page title, active nav item)."""

    page_title: str = ""
    nav_active: str = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx: dict[str, Any] = super().get_context_data(**kwargs)
        ctx["page_title"] = self.page_title
        ctx["nav_active"] = self.nav_active
        return ctx


class SingleRealtimeView(BasePageView):
    template_name: str = "web/single_realtime.html"
    page_title: str = "Real-Time"
    nav_active: str = "single_realtime"


class DashboardView(BasePageView):
    template_name: str = "web/home.html"
    page_title: str = "Dashboard"
    nav_active: str = "dashboard"


class RealtimeView(BasePageView):
    template_name: str = "web/realtime.html"
    page_title: str = "Gempa Real-time"
    nav_active: str = "realtime"


class FeltView(BasePageView):
    template_name: str = "web/felt.html"
    page_title: str = "Gempa Dirasakan"
    nav_active: str = "felt"


class TsunamiView(BasePageView):
    template_name: str = "web/tsunami.html"
    page_title: str = "Peringatan Tsunami"
    nav_active: str = "tsunami"


class M5View(BasePageView):
    template_name: str = "web/m5.html"
    page_title: str = "Gempa M5+"
    nav_active: str = "m5"


class DamageView(BasePageView):
    template_name: str = "web/damage.html"
    page_title: str = "Gempa Merusak"
    nav_active: str = "damage"
