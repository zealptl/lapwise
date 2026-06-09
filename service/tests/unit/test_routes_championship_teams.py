"""Unit tests for GET /v1/championship_teams."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
from lapwise.models.championship import ChampionshipTeam
from lapwise.services.championship import ChampionshipTeamService


def _make_entry(**overrides: object) -> ChampionshipTeam:
    defaults: dict[str, object] = {
        "meeting_key": 1219,
        "points_current": 860.0,
        "points_start": 835.0,
        "position_current": 1,
        "position_start": 1,
        "session_key": 9165,
        "team_name": "Red Bull Racing",
    }
    defaults.update(overrides)
    return ChampionshipTeam(**defaults)


def _fixture_client(mock_svc: ChampionshipTeamService) -> TestClient:
    from lapwise.deps import get_championship_team_service

    app = create_app()
    app.dependency_overrides[get_championship_team_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_championship_teams_returns_200() -> None:
    """GET /v1/championship_teams returns 200."""
    mock_svc = MagicMock(spec=ChampionshipTeamService)
    mock_svc.list_standings = AsyncMock(return_value=[_make_entry()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_teams")
    assert response.status_code == 200
    assert response.json()[0]["team_name"] == "Red Bull Racing"


def test_list_championship_teams_team_name_filter() -> None:
    """GET /v1/championship_teams?team_name=... forwards team_name."""
    mock_svc = MagicMock(spec=ChampionshipTeamService)
    mock_svc.list_standings = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_teams?team_name=Ferrari")
    assert response.status_code == 200
    assert mock_svc.list_standings.call_args.kwargs.get("team_name") == "Ferrari"


def test_list_championship_teams_latest_meeting_key() -> None:
    """GET /v1/championship_teams?meeting_key=latest forwards string 'latest'."""
    mock_svc = MagicMock(spec=ChampionshipTeamService)
    mock_svc.list_standings = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/championship_teams?meeting_key=latest")
    assert response.status_code == 200
    assert mock_svc.list_standings.call_args.kwargs.get("meeting_key") == "latest"


@respx.mock
def test_list_championship_teams_upstream_502() -> None:
    """GET /v1/championship_teams returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/championship_teams").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/championship_teams")
    assert response.status_code == 502
