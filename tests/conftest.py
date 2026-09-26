import os
from pathlib import Path

import pytest
import respx
from fastapi.testclient import TestClient

# Must be set before the app (and its cached settings) are imported.
UPSTREAM = "https://upstream.invalid/secret-bucket"
os.environ["BMKG_API"] = UPSTREAM
os.environ["SITE_URL"] = "https://gempa.example"

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.fixture
def upstream():
    """Mock every upstream feed with the recorded fixtures."""
    get_settings.cache_clear()
    with respx.mock(base_url=UPSTREAM, assert_all_called=False) as mock:
        for name in FIXTURES.iterdir():
            mock.get(f"/{name.name}").respond(200, content=name.read_bytes())
        yield mock


@pytest.fixture
def client(upstream):
    with TestClient(create_app()) as test_client:
        yield test_client
