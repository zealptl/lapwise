"""Unit tests for GET /v1/sessions."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.sessions import Session
from lapwise.services.sessions import SessionService


def _session_payload(**overrides: object) -> dict:
    base = {
        "circuit_key": 7,
        "circuit_short_name": "Spa",
        "country_code": "BEL",
        "country_key": 16,
        "country_name": "Belgium",
        "date_end": None,
        "date_start": None,
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Spa-Francorchamps",
        "meeting_key": 1216,
        "session_key": 9140,
        "session_name": "Sprint Qualifying",
        "session_type": "Qualifying",
        "year": 2023,
    }
    base.update(overrides)
    return base


def _make_session(**overrides: object) -> Session:
    return Session(**_session_payload(**overrides))


@pytest.fixture()
def mock_svc() -> SessionService:
    svc = MagicMock(spec=SessionService)
    svc.list_sessions = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: SessionService) -> TestClient:
    from lapwise.deps import get_session_service

    app = create_app()
    app.dependency_overrides[get_session_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_sessions_returns_200(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions returns 200 with a list of sessions."""
    mock_svc.list_sessions.return_value = [_make_session()]
    response = client.get("/v1/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["session_key"] == 9140


def test_list_sessions_equality_filter(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions?country_name=Belgium&year=2023 forwards filters to service."""
    mock_svc.list_sessions.return_value = [_make_session(country_name="Belgium")]
    response = client.get("/v1/sessions?country_name=Belgium&year=2023")
    assert response.status_code == 200
    mock_svc.list_sessions.assert_called_once()
    kwargs = mock_svc.list_sessions.call_args.kwargs
    assert kwargs.get("country_name") == "Belgium"
    assert kwargs.get("year") == 2023


def test_list_sessions_session_name_url_encoded(
    client: TestClient, mock_svc: SessionService
) -> None:
    """GET /v1/sessions?session_name=Sprint+Qualifying passes session_name to service."""
    mock_svc.list_sessions.return_value = [_make_session()]
    response = client.get("/v1/sessions?session_name=Sprint+Qualifying&year=2023")
    assert response.status_code == 200
    kwargs = mock_svc.list_sessions.call_args.kwargs
    assert kwargs.get("session_name") == "Sprint Qualifying"


def test_list_sessions_session_key_latest(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions?session_key=latest forwards the literal string latest to service."""
    mock_svc.list_sessions.return_value = [_make_session()]
    response = client.get("/v1/sessions?session_key=latest")
    assert response.status_code == 200
    kwargs = mock_svc.list_sessions.call_args.kwargs
    assert kwargs.get("session_key") == "latest"


def test_list_sessions_session_key_integer(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions?session_key=9140 works with integer session_key."""
    mock_svc.list_sessions.return_value = [_make_session()]
    response = client.get("/v1/sessions?session_key=9140")
    assert response.status_code == 200
    kwargs = mock_svc.list_sessions.call_args.kwargs
    assert kwargs.get("session_key") == 9140


def test_list_sessions_no_filters_returns_all(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions without filters calls service with all-None params."""
    payload = [_make_session(), _make_session(session_key=9141, session_name="Race")]
    mock_svc.list_sessions.return_value = payload
    response = client.get("/v1/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_sessions_session_key_invalid(client: TestClient, mock_svc: SessionService) -> None:
    """GET /v1/sessions?session_key=notanint returns 422."""
    response = client.get("/v1/sessions?session_key=notanint")
    assert response.status_code == 422


@respx.mock
def test_list_sessions_upstream_502() -> None:
    """GET /v1/sessions returns 502 when OpenF1 returns 503 (integration test)."""
    respx.get("https://api.openf1.org/v1/sessions").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/sessions")
    assert response.status_code == 502
    assert response.json()["detail"] == "OpenF1 upstream error"
