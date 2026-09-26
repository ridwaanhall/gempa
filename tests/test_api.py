import httpx
import pytest

from tests.conftest import UPSTREAM

LIST_ENDPOINTS = [
    "/api/v1/earthquakes/realtime",
    "/api/v1/earthquakes/felt",
    "/api/v1/earthquakes/damaging",
    "/api/v1/earthquakes/archive/3m",
    "/api/v1/tsunami",
    "/api/v1/stations/indonesia",
    "/api/v1/stations/global",
]


@pytest.mark.parametrize("path", LIST_ENDPOINTS)
def test_list_endpoints_use_envelope(client, path):
    response = client.get(path)
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["count"] == len(body["data"]) > 0
    assert body["meta"]["source"] == "BMKG"
    assert "s-maxage" in response.headers["cache-control"]


def test_latest(client):
    body = client.get("/api/v1/earthquakes/latest").json()
    assert body["data"]["event_id"] == "20260926023929"
    assert body["data"]["media"]["shakemap"].startswith("/api/v1/media/")


def test_realtime_filters(client):
    body = client.get("/api/v1/earthquakes/realtime", params={"limit": 1}).json()
    assert body["meta"]["count"] == 1
    body = client.get("/api/v1/earthquakes/realtime", params={"min_magnitude": 9.9}).json()
    assert body["data"] == []


def test_faults_geojson(client):
    body = client.get("/api/v1/faults/indonesia").json()
    assert body["type"] == "FeatureCollection"


def test_secret_never_leaks(client):
    """The upstream base URL must not appear in any response."""
    paths = [*LIST_ENDPOINTS, "/api/v1/earthquakes/latest", "/openapi.json", "/", "/tsunami/"]
    for path in paths:
        assert "upstream.invalid" not in client.get(path).text, path


def test_upstream_down_returns_502_without_url(client, upstream):
    upstream.get("/last30event.xml").mock(side_effect=httpx.ConnectError("boom"))
    response = client.get("/api/v1/earthquakes/significant")
    assert response.status_code == 502
    assert UPSTREAM not in response.text
    assert "upstream.invalid" not in response.text


def test_missing_narrative_is_404(client, upstream):
    upstream.get("/20260101000000_narasi.txt").respond(403)
    response = client.get("/api/v1/earthquakes/20260101000000/narrative")
    assert response.status_code == 404


def test_narrative_is_sanitised(client, upstream):
    upstream.get("/20260101000000_narasi.txt").respond(
        200, text='<p onclick="x()">Halo<script>alert(1)</script></p><p>&nbsp;</p><img src=x>'
    )
    html = client.get("/api/v1/earthquakes/20260101000000/narrative").json()["html"]
    assert html == "<p>Halo</p>"


def test_media_proxy(client, upstream):
    upstream.get("/20260926023929.mmi.jpg").respond(
        200, content=b"\xff\xd8jpeg", headers={"content-type": "image/jpeg"}
    )
    response = client.get("/api/v1/media/20260926023929/shakemap")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_media_rejects_non_images(client, upstream):
    upstream.get("/20260926023929.mmi.jpg").respond(
        200, text="<html>", headers={"content-type": "text/html"}
    )
    assert client.get("/api/v1/media/20260926023929/shakemap").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/media/../../etc/shakemap",
        "/api/v1/media/123/shakemap",
        "/api/v1/media/20260926023929/secrets",
        "/api/v1/earthquakes/archive/10y",
        "/api/v1/earthquakes/realtime/..%2Fx/history",
    ],
)
def test_path_validation(client, path):
    assert client.get(path).status_code in {404, 422}


def test_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
