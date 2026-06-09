"""Unit tests for GET /v1/overtakes."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.overtakes import Overtake
from lapwise.services.overtakes import OvertakeService


def _make_overtake(**overrides: object) -> Overtake:
    defaults: dict[str, object] = {
        "date": "2023-09-03T14:12:33+00:00",
        "meeting_key": 1219,
        "overtaken_driver_number": 4,
        "overtaking_driver_number": 63,
        "position": 3,
        "session_key": 9165,
    }
    defaults.update(overrides)
    return Overtake(**defaults)


def _fixture_client(mock_svc: OvertakeService) -> TestClient:
    from lapwise.deps import get_overtake_service

    app = create_app()
    app.dependency_overrides[get_overtake_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_overtakes_returns_200() -> None:
    """GET /v1/overtakes returns 200."""
    mock_svc = MagicMock(spec=OvertakeService)
    mock_svc.list_overtakes = AsyncMock(return_value=[_make_overtake()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/overtakes")
    assert response.status_code == 200
    assert response.json()[0]["overtaking_driver_number"] == 63


def test_list_overtakes_equality_filters() -> None:
    """GET /v1/overtakes?session_key=9636&position=1 forwards filters."""
    mock_svc = MagicMock(spec=OvertakeService)
    mock_svc.list_overtakes = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get(
        "/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4"
    )
    assert response.status_code == 200
    kwargs = mock_svc.list_overtakes.call_args.kwargs
    assert kwargs.get("session_key") == 9636
    assert kwargs.get("overtaking_driver_number") == 63
    assert kwargs.get("overtaken_driver_number") == 4


@respx.mock
def test_list_overtakes_upstream_502() -> None:
    """GET /v1/overtakes returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/overtakes").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/overtakes")
    assert response.status_code == 502
