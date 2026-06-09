"""Unit tests for GET /v1/pit."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.pit import PitStop
from lapwise.services.pit import PitService


def _make_pit(**overrides: object) -> PitStop:
    defaults: dict[str, object] = {
        "date": "2023-09-03T13:14:55+00:00",
        "driver_number": 1,
        "lane_duration": 23.227,
        "lap_number": 27,
        "meeting_key": 1219,
        "pit_duration": 23.227,
        "session_key": 9165,
        "stop_duration": 2.4,
    }
    defaults.update(overrides)
    return PitStop(**defaults)


@pytest.fixture()
def mock_svc() -> PitService:
    svc = MagicMock(spec=PitService)
    svc.list_pit_stops = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: PitService) -> TestClient:
    from lapwise.deps import get_pit_service

    app = create_app()
    app.dependency_overrides[get_pit_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_pit_stops_returns_200(client: TestClient, mock_svc: PitService) -> None:
    """GET /v1/pit returns 200."""
    mock_svc.list_pit_stops.return_value = [_make_pit()]
    response = client.get("/v1/pit")
    assert response.status_code == 200
    assert response.json()[0]["driver_number"] == 1


def test_list_pit_stops_comparison_filter(client: TestClient, mock_svc: PitService) -> None:
    """GET /v1/pit?stop_duration_lt=2.3 forwards comparison filter to service."""
    mock_svc.list_pit_stops.return_value = []
    response = client.get("/v1/pit?session_key=9877&stop_duration_lt=2.3")
    assert response.status_code == 200
    kwargs = mock_svc.list_pit_stops.call_args.kwargs
    assert kwargs.get("stop_duration_lt") == 2.3


def test_list_pit_stops_repeated_driver_number(client: TestClient, mock_svc: PitService) -> None:
    """GET /v1/pit?driver_number=1&driver_number=11 passes list[int]."""
    mock_svc.list_pit_stops.return_value = []
    response = client.get("/v1/pit?driver_number=1&driver_number=11")
    assert response.status_code == 200
    assert mock_svc.list_pit_stops.call_args.kwargs.get("driver_number") == [1, 11]


@respx.mock
def test_list_pit_stops_upstream_502() -> None:
    """GET /v1/pit returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/pit").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/pit")
    assert response.status_code == 502
