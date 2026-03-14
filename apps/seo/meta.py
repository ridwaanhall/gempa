"""SEO configuration — site-wide metadata, page definitions, and structured data."""

from __future__ import annotations

# ── Site-wide constants ──────────────────────────────────────

SITE_NAME = "Gempa Monitor"
SITE_DESCRIPTION = (
    "Monitor gempa bumi Indonesia secara real-time. "
    "Data resmi BMKG: gempa terkini, gempa dirasakan, gempa M5+, "
    "peringatan tsunami, dan gempa merusak."
)
SITE_KEYWORDS = (
    "gempa bumi, earthquake, BMKG, Indonesia, gempa terkini, "
    "gempa dirasakan, tsunami, seismologi, monitor gempa, "
    "earthquake monitoring, real-time earthquake, gempa hari ini"
)
SITE_AUTHOR = "ridwaanhall"
SITE_LOCALE = "id_ID"
SITE_THEME_COLOR = "#10b981"  # emerald-500
SITE_OG_TYPE = "website"
SITE_TWITTER_CARD = "summary_large_image"

# ── Per-page SEO metadata ───────────────────────────────────

PAGE_META: dict[str, dict[str, str]] = {
    "single_realtime": {
        "title": "Real-Time",
        "description": (
            "Gempa bumi terbaru dari jaringan sensor BMKG Indonesia. "
            "Data real-time satu gempa terkini dengan peta interaktif multi-layer."
        ),
        "keywords": "gempa real-time, gempa terbaru, live earthquake, BMKG sensor, gempa hari ini",
    },
    "dashboard": {
        "title": "Dashboard",
        "description": (
            "Dashboard monitor gempa bumi Indonesia — "
            "gempa terbaru, peta seismik, data sensor BMKG real-time."
        ),
        "keywords": "dashboard gempa, gempa terbaru, peta seismik Indonesia, BMKG",
    },
    "realtime": {
        "title": "Gempa Real-time",
        "description": (
            "200 gempa terkini dari jaringan sensor BMKG. "
            "Data real-time dengan peta interaktif dan tabel detail."
        ),
        "keywords": "gempa real-time, gempa terkini, live earthquake, BMKG sensor",
    },
    "felt": {
        "title": "Gempa Dirasakan",
        "description": (
            "Daftar 30 gempa terbaru yang dirasakan masyarakat Indonesia. "
            "Termasuk lokasi, magnitudo, kedalaman, dan laporan dirasakan."
        ),
        "keywords": "gempa dirasakan, felt earthquake, gempa terasa, laporan gempa",
    },
    "m5": {
        "title": "Gempa M5+",
        "description": (
            "Gempa bumi signifikan magnitudo 5 ke atas di Indonesia. "
            "Data 30 gempa M5+ terbaru dengan analisis BMKG."
        ),
        "keywords": "gempa M5, gempa besar, significant earthquake, gempa kuat Indonesia",
    },
    "tsunami": {
        "title": "Peringatan Tsunami",
        "description": (
            "Data peringatan dini tsunami BMKG Indonesia. "
            "Zona peringatan, observasi gelombang, dan analisis BMKG."
        ),
        "keywords": "peringatan tsunami, tsunami warning, BMKG tsunami, early warning",
    },
    "damage": {
        "title": "Gempa Merusak",
        "description": (
            "Katalog gempa merusak dan berpotensi tsunami di Indonesia. "
            "Data historis dengan statistik korban dan kerusakan."
        ),
        "keywords": "gempa merusak, destructive earthquake, kerusakan gempa, katalog gempa",
    },
}

# ── JSON-LD structured data templates ────────────────────────

def build_website_jsonld(site_url: str) -> dict:
    """Build JSON-LD ``WebSite`` schema for the homepage."""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "description": SITE_DESCRIPTION,
        "url": site_url,
        "inLanguage": "id-ID",
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": site_url,
        },
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{site_url}realtime/",
            "query-input": "required name=search_term_string",
        },
    }


def build_webpage_jsonld(
    site_url: str,
    page_url: str,
    title: str,
    description: str,
) -> dict:
    """Build JSON-LD ``WebPage`` schema for any page."""
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{title} — {SITE_NAME}",
        "description": description,
        "url": page_url,
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": site_url,
        },
        "inLanguage": "id-ID",
        "about": {
            "@type": "Thing",
            "name": "Earthquake Monitoring",
            "description": "Real-time earthquake monitoring data from BMKG Indonesia",
        },
    }


def build_breadcrumb_jsonld(site_url: str, items: list[tuple[str, str]]) -> dict:
    """Build JSON-LD ``BreadcrumbList`` schema.

    *items* is a list of ``(name, relative_path)`` tuples.
    """
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": f"{site_url}{path}",
            }
            for i, (name, path) in enumerate(items)
        ],
    }
