"""Unit tests for GET /v1/stints."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.stints import Stint
from lapwise.services.stints import StintService


def _make_stint(**overrides: object) -> Stint:
    defaults: dict[str, object] = {
        "compound": "SOFT",
        "driver_number": 1,
        "lap_end": 27,
        "lap_start": 1,
        "meeting_key": 1219,
        "session_key": 9165,
        "stint_number": 1,
        "tyre_age_at_start": 0,
    }
    defaults.update(overrides)
    return Stint(**defaults)


def _fixture_client(mock_svc: StintService) -> TestClient:
    from lapwise.deps import get_stint_service

    app = create_app()
    app.dependency_overrides[get_stint_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_stints_returns_200() -> None:
    """GET /v1/stints returns 200."""
    mock_svc = MagicMock(spec=StintService)
    mock_svc.list_stints = AsyncMock(return_value=[_make_stint()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/stints")
    assert response.status_code == 200
    assert response.json()[0]["compound"] == "SOFT"


def test_list_stints_comparison_filter() -> None:
    """GET /v1/stints?tyre_age_at_start_gte=3 forwards comparison filter."""
    mock_svc = MagicMock(spec=StintService)
    mock_svc.list_stints = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/stints?session_key=9165&tyre_age_at_start_gte=3")
    assert response.status_code == 200
    assert mock_svc.list_stints.call_args.kwargs.get("tyre_age_at_start_gte") == 3


def test_list_stints_repeated_driver_number() -> None:
    """GET /v1/stints?driver_number=1&driver_number=11 passes list[int]."""
    mock_svc = MagicMock(spec=StintService)
    mock_svc.list_stints = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/stints?driver_number=1&driver_number=11")
    assert response.status_code == 200
    assert mock_svc.list_stints.call_args.kwargs.get("driver_number") == [1, 11]


@respx.mock
def test_list_stints_upstream_502() -> None:
    """GET /v1/stints returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/stints").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/stints")
    assert response.status_code == 502
