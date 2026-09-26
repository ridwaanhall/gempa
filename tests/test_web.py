from html import escape

import pytest

from app.web.pages import PAGES


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.key)
def test_pages_render(client, page):
    response = client.get(page.path)
    assert response.status_code == 200
    html = response.text
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
