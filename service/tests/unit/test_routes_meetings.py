"""Unit tests for GET /v1/meetings."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.meetings import Meeting
from lapwise.services.meetings import MeetingService


def _make_meeting(**overrides: object) -> Meeting:
    defaults: dict[str, object] = {
        "circuit_key": 16,
        "circuit_info_url": None,
        "circuit_image": None,
        "circuit_short_name": "Monza",
        "circuit_type": "permanent",
        "country_code": "ITA",
        "country_flag": None,
        "country_key": 13,
        "country_name": "Italy",
        "date_end": None,
        "date_start": None,
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Monza",
        "meeting_key": 1219,
        "meeting_name": "Italian Grand Prix",
        "meeting_official_name": None,
        "year": 2023,
    }
    defaults.update(overrides)
    return Meeting(**defaults)


@pytest.fixture()
def mock_svc() -> MeetingService:
    svc = MagicMock(spec=MeetingService)
    svc.list_meetings = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: MeetingService) -> TestClient:
    from lapwise.deps import get_meeting_service

    app = create_app()
    app.dependency_overrides[get_meeting_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_meetings_returns_200(client: TestClient, mock_svc: MeetingService) -> None:
    """GET /v1/meetings returns 200 with a list of meetings."""
    mock_svc.list_meetings.return_value = [_make_meeting()]
    response = client.get("/v1/meetings")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["meeting_key"] == 1219


def test_list_meetings_equality_filter(client: TestClient, mock_svc: MeetingService) -> None:
    """GET /v1/meetings?year=2023&country_name=Italy forwards filters to service."""
    mock_svc.list_meetings.return_value = [_make_meeting()]
    response = client.get("/v1/meetings?year=2023&country_name=Italy")
    assert response.status_code == 200
    kwargs = mock_svc.list_meetings.call_args.kwargs
    assert kwargs.get("year") == 2023
    assert kwargs.get("country_name") == "Italy"


def test_list_meetings_meeting_key_latest(client: TestClient, mock_svc: MeetingService) -> None:
    """GET /v1/meetings?meeting_key=latest forwards the literal string latest to service."""
    mock_svc.list_meetings.return_value = [_make_meeting()]
    response = client.get("/v1/meetings?meeting_key=latest")
    assert response.status_code == 200
    kwargs = mock_svc.list_meetings.call_args.kwargs
    assert kwargs.get("meeting_key") == "latest"


def test_list_meetings_meeting_key_integer(client: TestClient, mock_svc: MeetingService) -> None:
    """GET /v1/meetings?meeting_key=1219 works with integer meeting_key."""
    mock_svc.list_meetings.return_value = [_make_meeting()]
    response = client.get("/v1/meetings?meeting_key=1219")
    assert response.status_code == 200
    kwargs = mock_svc.list_meetings.call_args.kwargs
    assert kwargs.get("meeting_key") == 1219


def test_list_meetings_no_filters(client: TestClient, mock_svc: MeetingService) -> None:
    """GET /v1/meetings without filters returns all meetings."""
    mock_svc.list_meetings.return_value = [_make_meeting(), _make_meeting(meeting_key=1220)]
    response = client.get("/v1/meetings")
    assert response.status_code == 200
    assert len(response.json()) == 2


@respx.mock
def test_list_meetings_upstream_502() -> None:
    """GET /v1/meetings returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/meetings").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/meetings")
    assert response.status_code == 502
    assert response.json()["detail"] == "OpenF1 upstream error"
