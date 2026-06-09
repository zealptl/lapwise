"""Unit tests for ChampionshipTeamService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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


@pytest.mark.asyncio
async def test_list_standings_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_entry()]
    client.get = AsyncMock(return_value=expected)

    service = ChampionshipTeamService(client)
    result = await service.list_standings(session_key="latest", team_name="Red Bull Racing")

    client.get.assert_called_once_with(
        "championship_teams",
        ChampionshipTeam,
        session_key="latest",
        team_name="Red Bull Racing",
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_standings_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = ChampionshipTeamService(client)
    result = await service.list_standings()

    assert result == []
