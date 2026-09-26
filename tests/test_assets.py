"""Static URLs are content-hashed and every ES-module import resolves through the import map."""

import base64
import hashlib
import json
import re

from app.core.assets import STATIC_DIR, static_url

_IMPORTMAP = re.compile(r'<script type="importmap"[^>]*>(.*?)</script>', re.S)
_IMPORT = re.compile(r"""(?:^|\s)(?:import|export)\b[^'"]*?from\s*['"]([^'"]+)['"]""", re.M)


def _page_map(client) -> tuple[str, dict[str, str], str]:
    response = client.get("/")
    raw = _IMPORTMAP.search(response.text).group(1)
    return raw, json.loads(raw)["imports"], response.headers["content-security-policy"]


def test_static_url_is_content_hashed():
    url = static_url("css/app.css")
    digest = hashlib.sha256((STATIC_DIR / "css/app.css").read_bytes()).hexdigest()[:10]
    assert url == f"/static/css/app.css?v={digest}"


def test_import_map_precedes_module_scripts(client):
    html = client.get("/").text
    assert html.index('type="importmap"') < html.index('type="module"')


def test_inline_import_map_is_allowed_by_csp(client):
    raw, _, csp = _page_map(client)
    digest = base64.b64encode(hashlib.sha256(raw.encode()).digest()).decode()
    assert f"'sha256-{digest}'" in csp
    assert "'unsafe-inline'" not in csp.split("script-src", 1)[1].split(";", 1)[0]


def test_every_module_import_is_versioned(client):
    """A relative import that the map misses would load unversioned (and could be stale)."""
    _, imports, _ = _page_map(client)
    for path in (STATIC_DIR / "js").rglob("*.js"):
        for spec in _IMPORT.findall(path.read_text(encoding="utf-8")):
            target = (path.parent / spec).resolve().relative_to(STATIC_DIR).as_posix()
            key = f"/static/{target}"
            assert key in imports, f"{path.name} imports {spec}: not in import map"
            assert imports[key] == static_url(target)
