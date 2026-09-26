"""Content-hashed static URLs and the ES-module import map.

Every static URL carries `?v=<hash of that file>`, so a URL only changes when its file
does and versioned responses can be cached forever. Module scripts import each other
with bare relative paths (`./lib/api.js`); the import map rewrites every one of those
to its hashed URL, so a deploy can never mix a fresh page script with a stale module.
"""

import base64
import hashlib
import json
from functools import cache
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_JS_DIR = STATIC_DIR / "js"


@cache
def _file_hash(relpath: str) -> str:
    return hashlib.sha256((STATIC_DIR / relpath).read_bytes()).hexdigest()[:10]


def static_url(relpath: str) -> str:
    """`static_url("css/app.css")` → `/static/css/app.css?v=<content hash>`."""
    relpath = relpath.lstrip("/")
    return f"/static/{relpath}?v={_file_hash(relpath)}"


@cache
def import_map() -> str:
    """The `<script type="importmap">` body: every JS module → its hashed URL."""
    imports = {}
    for path in sorted(_JS_DIR.rglob("*.js")):
        rel = path.relative_to(STATIC_DIR).as_posix()
        imports[f"/static/{rel}"] = static_url(rel)
    return json.dumps({"imports": imports}, separators=(",", ":"))


@cache
def import_map_csp_hash() -> str:
    """CSP source allowing the inline import map (and nothing else inline)."""
    digest = hashlib.sha256(import_map().encode()).digest()
    return f"'sha256-{base64.b64encode(digest).decode()}'"
