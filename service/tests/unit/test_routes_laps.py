"""Unit tests for GET /v1/laps."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.laps import Lap
from lapwise.services.laps import LapService


def _make_lap(**overrides: object) -> Lap:
    defaults: dict[str, object] = {
        "date_start": None,
        "driver_number": 1,
        "duration_sector_1": 26.966,
        "duration_sector_2": 38.657,
        "duration_sector_3": 26.14,
        "i1_speed": 307,
        "i2_speed": 277,
        "is_pit_out_lap": False,
        "lap_duration": 91.763,
        "lap_number": 8,
        "meeting_key": 1219,
        "segments_sector_1": None,
        "segments_sector_2": None,
        "segments_sector_3": None,
        "session_key": 9161,
        "st_speed": 298,
    }
    defaults.update(overrides)
    return Lap(**defaults)


@pytest.fixture()
def mock_svc() -> LapService:
    svc = MagicMock(spec=LapService)
    svc.list_laps = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: LapService) -> TestClient:
    from lapwise.deps import get_lap_service

    app = create_app()
    app.dependency_overrides[get_lap_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_laps_returns_200(client: TestClient, mock_svc: LapService) -> None:
    """GET /v1/laps returns 200 with a list of laps."""
    mock_svc.list_laps.return_value = [_make_lap()]
    response = client.get("/v1/laps")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["lap_number"] == 8


def test_list_laps_comparison_filter(client: TestClient, mock_svc: LapService) -> None:
    """GET /v1/laps?session_key=9161&lap_duration_lt=92.0 forwards filters to service."""
    mock_svc.list_laps.return_value = [_make_lap()]
    response = client.get("/v1/laps?session_key=9161&lap_duration_lt=92.0")
    assert response.status_code == 200
    kwargs = mock_svc.list_laps.call_args.kwargs
    assert kwargs.get("session_key") == 9161
    assert kwargs.get("lap_duration_lt") == 92.0


def test_list_laps_repeated_driver_number(client: TestClient, mock_svc: LapService) -> None:
    """GET /v1/laps?driver_number=63&driver_number=44 passes list[int] to service."""
    mock_svc.list_laps.return_value = []
    response = client.get("/v1/laps?driver_number=63&driver_number=44")
    assert response.status_code == 200
    kwargs = mock_svc.list_laps.call_args.kwargs
    assert kwargs.get("driver_number") == [63, 44]


def test_list_laps_no_filters(client: TestClient, mock_svc: LapService) -> None:
    """GET /v1/laps without filters returns 200."""
    mock_svc.list_laps.return_value = [_make_lap(), _make_lap(lap_number=9)]
    response = client.get("/v1/laps")
    assert response.status_code == 200
    assert len(response.json()) == 2


@respx.mock
def test_list_laps_upstream_502() -> None:
    """GET /v1/laps returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/laps").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/laps")
    assert response.status_code == 502
    assert response.json()["detail"] == "OpenF1 upstream error"
