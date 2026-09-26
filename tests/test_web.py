from html import escape

import pytest

from app.web.pages import PAGES


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.key)
def test_pages_render(client, page):
    response = client.get(page.path)
    assert response.status_code == 200
    html = response.text
    if page.key == "home":
        # Title leads with the latest earthquake from the fixture.
        assert "<title>Gempa terkini M4,9 Pusat gempa berada di laut" in html
        assert 'id="initial-data"' in html
    else:
        assert f"<title>{escape(page.title, quote=False)}" in html
    assert f'<link rel="canonical" href="https://gempa.example{page.path}">' in html
    assert "/static/css/app.css?v=" in html
    assert "tailwind" not in html.lower()


def test_security_headers(client):
    headers = client.get("/").headers
    assert "default-src 'self'" in headers["content-security-policy"]
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"


def test_api_is_noindex_and_docs_have_no_csp(client):
    assert client.get("/api/v1/health").headers["x-robots-tag"] == "noindex"
    assert "content-security-policy" not in client.get("/docs").headers


def test_static_css_served(client):
    response = client.get("/static/css/app.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_robots_and_sitemap(client):
    assert "Sitemap: https://gempa.example/sitemap.xml" in client.get("/robots.txt").text
    sitemap = client.get("/sitemap.xml").text
    for page in PAGES:
        assert f"<loc>https://gempa.example{page.path}</loc>" in sitemap


def test_html_404(client):
    response = client.get("/nope", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "Halaman tidak ditemukan" in response.text


def test_json_404(client):
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_legacy_dashboard_redirects(client):
    response = client.get("/dashboard/", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/map/"


def test_primary_content_is_server_rendered(client):
    """Crawlers get real content, not skeletons."""
    assert "Pusat gempa berada di laut 46 km utara Ruteng-Manggarai" in client.get("/").text
    assert "Flores Region, Indonesia" in client.get("/realtime/").text
    assert "Kab. Manggarai" in client.get("/felt/").text
    assert "MBAY-NAGEKEO-NTT" in client.get("/tsunami/").text


def test_pages_render_when_upstream_is_down(client, upstream):
    import httpx

    upstream.clear()
    upstream.route().mock(side_effect=httpx.ConnectError("down"))
    for path in ["/", "/realtime/", "/felt/", "/m5/", "/tsunami/", "/damage/"]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert 'id="initial-data"' not in response.text


def test_seo_tags(client):
    html = client.get("/tsunami/").text
    assert '<meta property="og:image" content="https://gempa.example/static/img/og.png">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert '"@type": "BreadcrumbList"' in html
    assert '"@type": "Dataset"' in client.get("/about/").text
