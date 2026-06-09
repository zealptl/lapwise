"""Unit tests for GET /v1/championship_drivers."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.championship import ChampionshipDriver
from lapwise.services.championship import ChampionshipDriverService


def _make_entry(**overrides: object) -> ChampionshipDriver:
    defaults: dict[str, object] = {
        "driver_number": 1,
        "meeting_key": 1219,
        "points_current": 331.0,
        "points_start": 306.0,
        "position_current": 1,
        "position_start": 1,
        "session_key": 9165,
    }
    defaults.update(overrides)
    return ChampionshipDriver(**defaults)


def _fixture_client(mock_svc: ChampionshipDriverService) -> TestClient:
    from lapwise.deps import get_championship_driver_service

    app = create_app()
    app.dependency_overrides[get_championship_driver_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_championship_drivers_returns_200() -> None:
    """GET /v1/championship_drivers returns 200."""
    mock_svc = MagicMock(spec=ChampionshipDriverService)
    mock_svc.list_standings = AsyncMock(return_value=[_make_entry()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_drivers")
    assert response.status_code == 200
    assert response.json()[0]["driver_number"] == 1


def test_list_championship_drivers_latest_session_key() -> None:
    """GET /v1/championship_drivers?session_key=latest forwards string 'latest'."""
    mock_svc = MagicMock(spec=ChampionshipDriverService)
    mock_svc.list_standings = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_drivers?session_key=latest")
    assert response.status_code == 200
    assert mock_svc.list_standings.call_args.kwargs.get("session_key") == "latest"


def test_list_championship_drivers_repeated_driver_number() -> None:
    """GET /v1/championship_drivers?driver_number=1&driver_number=11 passes list[int]."""
    mock_svc = MagicMock(spec=ChampionshipDriverService)
    mock_svc.list_standings = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_drivers?driver_number=1&driver_number=11")
    assert response.status_code == 200
    assert mock_svc.list_standings.call_args.kwargs.get("driver_number") == [1, 11]


@respx.mock
def test_list_championship_drivers_upstream_502() -> None:
    """GET /v1/championship_drivers returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/championship_drivers").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/championship_drivers")
    assert response.status_code == 502
