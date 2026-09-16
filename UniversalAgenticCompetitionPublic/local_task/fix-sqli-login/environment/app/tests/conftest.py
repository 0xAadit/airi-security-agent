import httpx
import pytest


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url="http://localhost:8000", timeout=10.0)
