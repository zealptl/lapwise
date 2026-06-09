"""Unit tests for GET /v1/drivers."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.drivers import Driver
from lapwise.services.drivers import DriverService


def _make_driver(**overrides: object) -> Driver:
    defaults: dict[str, object] = {
        "broadcast_name": "M VERSTAPPEN",
        "country_code": "NED",
        "driver_number": 1,
        "first_name": "Max",
        "full_name": "Max Verstappen",
        "headshot_url": None,
        "last_name": "Verstappen",
        "meeting_key": 1216,
        "name_acronym": "VER",
        "session_key": 9140,
        "team_colour": "3671C6",
        "team_name": "Red Bull Racing",
    }
    defaults.update(overrides)
    return Driver(**defaults)


@pytest.fixture()
def mock_svc() -> DriverService:
    svc = MagicMock(spec=DriverService)
    svc.list_drivers = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: DriverService) -> TestClient:
    from lapwise.deps import get_driver_service

    app = create_app()
    app.dependency_overrides[get_driver_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_drivers_returns_200(client: TestClient, mock_svc: DriverService) -> None:
    """GET /v1/drivers returns 200 with a list of drivers."""
    mock_svc.list_drivers.return_value = [_make_driver()]
    response = client.get("/v1/drivers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["driver_number"] == 1


def test_list_drivers_equality_filter(client: TestClient, mock_svc: DriverService) -> None:
    """GET /v1/drivers?session_key=9140&team_name=... forwards filters."""
    mock_svc.list_drivers.return_value = [_make_driver()]
    response = client.get("/v1/drivers?session_key=9140&team_name=Red+Bull+Racing")
    assert response.status_code == 200
    kwargs = mock_svc.list_drivers.call_args.kwargs
    assert kwargs.get("session_key") == 9140
    assert kwargs.get("team_name") == "Red Bull Racing"


def test_list_drivers_repeated_driver_number(client: TestClient, mock_svc: DriverService) -> None:
    """GET /v1/drivers?driver_number=1&driver_number=11 passes list[int] to service."""
    mock_svc.list_drivers.return_value = []
    response = client.get("/v1/drivers?driver_number=1&driver_number=11")
    assert response.status_code == 200
    kwargs = mock_svc.list_drivers.call_args.kwargs
    assert kwargs.get("driver_number") == [1, 11]


def test_list_drivers_no_filters(client: TestClient, mock_svc: DriverService) -> None:
    """GET /v1/drivers without filters calls service with all-None params."""
    mock_svc.list_drivers.return_value = [_make_driver(), _make_driver(driver_number=11)]
    response = client.get("/v1/drivers")
    assert response.status_code == 200
    assert len(response.json()) == 2


@respx.mock
def test_list_drivers_upstream_502() -> None:
    """GET /v1/drivers returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/drivers")
    assert response.status_code == 502
    assert response.json()["detail"] == "OpenF1 upstream error"
