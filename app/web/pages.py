"""Page registry: one entry per HTML page. Drives routes, navigation, SEO and sitemap."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page:
    key: str
    path: str
    template: str
    nav_label: str
    title: str
    description: str
    changefreq: str = "hourly"
    priority: float = 0.8
    in_nav: bool = True


SITE_NAME = "Gempa"
SITE_TAGLINE = "Monitor gempa bumi Indonesia"
SITE_DESCRIPTION = (
    "Pantau gempa bumi di Indonesia secara real-time dari data resmi BMKG: gempa terkini, "
    "gempa dirasakan, gempa M5+, peringatan dini tsunami, dan katalog gempa merusak."
)

PAGES: tuple[Page, ...] = (
    Page(
        key="home",
        path="/",
        template="pages/home.html",
        nav_label="Terkini",
        title="Gempa bumi terkini di Indonesia",
        description=(
            "Gempa bumi terbaru yang dirasakan di Indonesia beserta deteksi real-time "
            "jaringan seismik BMKG, diperbarui setiap menit."
        ),
        changefreq="always",
        priority=1.0,
    ),
    Page(
        key="realtime",
        path="/realtime/",
        template="pages/realtime.html",
        nav_label="Realtime",
        title="Deteksi gempa real-time",
        description=(
            "Deteksi otomatis gempa bumi dari jaringan sensor BMKG: magnitudo, kedalaman, "
            "lokasi, dan riwayat pemutakhiran tiap kejadian."
        ),
        changefreq="always",
        priority=0.9,
    ),
    Page(
        key="felt",
        path="/felt/",
        template="pages/alerts.html",
        nav_label="Dirasakan",
        title="Gempa dirasakan",
        description=(
            "30 gempa bumi terakhir yang dirasakan masyarakat Indonesia, lengkap dengan "
            "skala intensitas MMI dan peta guncangan."
        ),
    ),
    Page(
        key="significant",
        path="/m5/",
        template="pages/alerts.html",
        nav_label="M5+",
        title="Gempa magnitudo 5 ke atas",
        description=(
            "30 gempa bumi terakhir bermagnitudo 5,0 atau lebih di wilayah Indonesia, "
            "dengan analisis dan narasi BMKG."
        ),
    ),
    Page(
        key="tsunami",
        path="/tsunami/",
        template="pages/tsunami.html",
        nav_label="Tsunami",
        title="Peringatan dini tsunami",
        description=(
            "Riwayat peringatan dini tsunami BMKG: status per wilayah, pengamatan tinggi "
            "gelombang, dan kronologi buletin."
        ),
        priority=0.9,
    ),
    Page(
        key="damaging",
        path="/damage/",
        template="pages/damage.html",
        nav_label="Merusak",
        title="Katalog gempa merusak",
        description=(
            "Katalog historis gempa bumi merusak di Indonesia sejak 1920-an: korban, "
            "kerusakan, dan tsunami yang ditimbulkan."
        ),
        changefreq="weekly",
        priority=0.6,
    ),
    Page(
        key="map",
        path="/map/",
        template="pages/map.html",
        nav_label="Peta",
        title="Peta seismisitas",
        description=(
            "Peta interaktif seismisitas Indonesia: gempa 3 bulan dan 5 tahun terakhir, "
            "stasiun seismik, dan jalur sesar aktif."
        ),
        changefreq="daily",
        priority=0.7,
    ),
    Page(
        key="about",
        path="/about/",
        template="pages/about.html",
        nav_label="Tentang",
        title="Tentang data & API",
        description=(
            "Cara membaca data gempa BMKG: magnitudo, skala MMI, zona waktu, dan API JSON "
            "terbuka yang dipakai situs ini."
        ),
        changefreq="monthly",
        priority=0.4,
    ),
)

PAGES_BY_KEY = {page.key: page for page in PAGES}
