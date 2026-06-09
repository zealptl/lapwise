"""Unit tests for GET /v1/starting_grid."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.services.starting_grid import StartingGridService


def _make_entry(**overrides: object) -> StartingGridEntry:
    defaults: dict[str, object] = {
        "driver_number": 1,
        "lap_duration": 83.404,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9165,
    }
    defaults.update(overrides)
    return StartingGridEntry(**defaults)


def _fixture_client(mock_svc: StartingGridService) -> TestClient:
    from lapwise.deps import get_starting_grid_service

    app = create_app()
    app.dependency_overrides[get_starting_grid_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_starting_grid_returns_200() -> None:
    """GET /v1/starting_grid returns 200."""
    mock_svc = MagicMock(spec=StartingGridService)
    mock_svc.list_grid = AsyncMock(return_value=[_make_entry()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/starting_grid")
    assert response.status_code == 200
    assert response.json()[0]["position"] == 1


def test_list_starting_grid_position_comparison_filter() -> None:
    """GET /v1/starting_grid?position_lte=10 forwards comparison filter."""
    mock_svc = MagicMock(spec=StartingGridService)
    mock_svc.list_grid = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/starting_grid?session_key=9165&position_lte=10")
    assert response.status_code == 200
    assert mock_svc.list_grid.call_args.kwargs.get("position_lte") == 10


def test_list_starting_grid_repeated_driver_number() -> None:
    """GET /v1/starting_grid?driver_number=1&driver_number=11 passes list[int]."""
    mock_svc = MagicMock(spec=StartingGridService)
    mock_svc.list_grid = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/starting_grid?driver_number=1&driver_number=11")
    assert response.status_code == 200
    assert mock_svc.list_grid.call_args.kwargs.get("driver_number") == [1, 11]


@respx.mock
def test_list_starting_grid_upstream_502() -> None:
    """GET /v1/starting_grid returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/starting_grid").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/starting_grid")
    assert response.status_code == 502
