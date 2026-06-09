"""Unit tests for GET /v1/session_result."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.session_result import SessionResult
from lapwise.services.session_result import SessionResultService


def _make_result(**overrides: object) -> SessionResult:
    defaults: dict[str, object] = {
        "dnf": False,
        "dns": False,
        "dsq": False,
        "driver_number": 1,
        "duration": 5412.234,
        "gap_to_leader": None,
        "number_of_laps": 53,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9161,
    }
    defaults.update(overrides)
    return SessionResult(**defaults)


@pytest.fixture()
def mock_svc() -> SessionResultService:
    svc = MagicMock(spec=SessionResultService)
    svc.list_results = AsyncMock(return_value=[])
    return svc


@pytest.fixture()
def client(mock_svc: SessionResultService) -> TestClient:
    from lapwise.deps import get_session_result_service

    app = create_app()
    app.dependency_overrides[get_session_result_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_results_returns_200(client: TestClient, mock_svc: SessionResultService) -> None:
    """GET /v1/session_result returns 200."""
    mock_svc.list_results.return_value = [_make_result()]
    response = client.get("/v1/session_result")
    assert response.status_code == 200
    assert response.json()[0]["position"] == 1


def test_list_results_equality_filters(client: TestClient, mock_svc: SessionResultService) -> None:
    """GET /v1/session_result?session_key=9161&position=1 forwards filters."""
    mock_svc.list_results.return_value = [_make_result()]
    response = client.get("/v1/session_result?session_key=9161&position=1")
    assert response.status_code == 200
    kwargs = mock_svc.list_results.call_args.kwargs
    assert kwargs.get("session_key") == 9161
    assert kwargs.get("position") == 1


def test_list_results_position_lte(client: TestClient, mock_svc: SessionResultService) -> None:
    """GET /v1/session_result?position_lte=3 passes comparison filter to service."""
    mock_svc.list_results.return_value = []
    response = client.get("/v1/session_result?session_key=9161&position_lte=3")
    assert response.status_code == 200
    kwargs = mock_svc.list_results.call_args.kwargs
    assert kwargs.get("position_lte") == 3


def test_list_results_repeated_driver_number(
    client: TestClient, mock_svc: SessionResultService
) -> None:
    """GET /v1/session_result?driver_number=1&driver_number=11 passes list[int]."""
    mock_svc.list_results.return_value = []
    response = client.get("/v1/session_result?driver_number=1&driver_number=11")
    assert response.status_code == 200
    kwargs = mock_svc.list_results.call_args.kwargs
    assert kwargs.get("driver_number") == [1, 11]


@respx.mock
def test_list_results_upstream_502() -> None:
    """GET /v1/session_result returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/session_result").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/session_result")
    assert response.status_code == 502
    assert response.json()["detail"] == "OpenF1 upstream error"
