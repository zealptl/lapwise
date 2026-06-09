"""Unit tests for the app-foundation capability.

Tests cover:
- GET /healthz returns 200 {"status": "ok"}
- OpenAPI schema includes expected tags with non-empty descriptions
- UpstreamError exception handler translates categories correctly
"""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from lapwise.clients.errors import UpstreamError
from lapwise.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient for the Lapwise app."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def client_with_error_routes() -> TestClient:
    """Return a TestClient with extra routes that raise UpstreamError for testing the handler."""
    app = create_app()

    test_router = APIRouter()

    @test_router.get("/test/bad-gateway")
    async def bad_gateway_route() -> dict[str, str]:
        raise UpstreamError(
            "bad_gateway",
            upstream_status=503,
            upstream_message="Service Unavailable",
        )

    @test_router.get("/test/gateway-timeout")
    async def gateway_timeout_route() -> dict[str, str]:
        raise UpstreamError("gateway_timeout")

    @test_router.get("/test/forwarded")
    async def forwarded_route() -> dict[str, str]:
        raise UpstreamError(
            "forwarded",
            upstream_status=404,
            upstream_message="Not Found",
        )

    app.include_router(test_router)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 3.6.1 — healthz
# ---------------------------------------------------------------------------


def test_healthz_returns_200(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 3.6.2 — OpenAPI tags
# ---------------------------------------------------------------------------


def test_openapi_tags_contain_openf1_wrappers(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    tag_names = {tag["name"] for tag in schema.get("tags", [])}
    assert "OpenF1 wrappers" in tag_names
    assert "Analysis" in tag_names


def test_openapi_tags_have_non_empty_descriptions(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    tags_by_name = {tag["name"]: tag for tag in schema.get("tags", [])}
    for name in ("OpenF1 wrappers", "Analysis"):
        assert name in tags_by_name, f"Tag '{name}' missing from OpenAPI schema"
        description = tags_by_name[name].get("description", "")
        assert description, f"Tag '{name}' has an empty description"


# ---------------------------------------------------------------------------
# 3.6.3 — bad_gateway → 502
# ---------------------------------------------------------------------------


def test_upstream_bad_gateway_returns_502(client_with_error_routes: TestClient) -> None:
    response = client_with_error_routes.get("/test/bad-gateway")
    assert response.status_code == 502
    body = response.json()
    assert body["detail"] == "OpenF1 upstream error"
    assert body["upstream_status"] == 503
    assert body["upstream_message"] == "Service Unavailable"


# ---------------------------------------------------------------------------
# 3.6.4 — gateway_timeout → 504
# ---------------------------------------------------------------------------


def test_upstream_gateway_timeout_returns_504(client_with_error_routes: TestClient) -> None:
    response = client_with_error_routes.get("/test/gateway-timeout")
    assert response.status_code == 504
    body = response.json()
    assert body["detail"] == "OpenF1 upstream error"
    assert body["upstream_status"] is None


# ---------------------------------------------------------------------------
# 3.6.5 — forwarded → original upstream status
# ---------------------------------------------------------------------------


def test_upstream_forwarded_returns_original_status(client_with_error_routes: TestClient) -> None:
    response = client_with_error_routes.get("/test/forwarded")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "OpenF1 upstream error"
    assert body["upstream_status"] == 404
    assert body["upstream_message"] == "Not Found"
