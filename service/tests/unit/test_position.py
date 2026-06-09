"""Unit tests for the endpoint-position capability."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.position import Position
from lapwise.services.position import PositionService

# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_positions_forwards_filters() -> None:
    """list_positions forwards all filters to the OpenF1 client."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])
    service = PositionService(mock_client)

    await service.list_positions(meeting_key=1217, driver_number=[40], position_lte=3)

    mock_client.get.assert_awaited_once_with(
        "position",
        Position,
        session_key=None,
        meeting_key=1217,
        driver_number=[40],
        position=None,
        position_lt=None,
        position_lte=3,
        position_gt=None,
        position_gte=None,
    )


@pytest.mark.asyncio
async def test_list_positions_returns_models() -> None:
    """list_positions returns parsed Position models."""
    pos = Position(
        date="2023-08-27T11:00:03Z",
        driver_number=1,
        meeting_key=1217,
        position=1,
        session_key=9149,
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[pos])
    service = PositionService(mock_client)

    result = await service.list_positions(session_key=9149)

    assert result == [pos]


# ---------------------------------------------------------------------------
# Route integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient for the Lapwise app."""
    return TestClient(create_app())


def test_position_route_registered(client: TestClient) -> None:
    """GET /v1/position is registered in the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/v1/position" in paths


def test_position_route_tag(client: TestClient) -> None:
    """GET /v1/position is tagged as OpenF1 wrappers."""
    response = client.get("/openapi.json")
    schema = response.json()
    get_op = schema["paths"]["/v1/position"]["get"]
    assert "OpenF1 wrappers" in get_op["tags"]


def test_position_route_has_502_and_504(client: TestClient) -> None:
    """GET /v1/position schema includes 502 and 504 response shapes."""
    response = client.get("/openapi.json")
    schema = response.json()
    responses = schema["paths"]["/v1/position"]["get"]["responses"]
    assert "502" in responses
    assert "504" in responses


def test_position_route_position_lte_param(client: TestClient) -> None:
    """GET /v1/position has position_lte query parameter."""
    response = client.get("/openapi.json")
    schema = response.json()
    params = schema["paths"]["/v1/position"]["get"]["parameters"]
    param_names = [p["name"] for p in params]
    assert "position_lte" in param_names
