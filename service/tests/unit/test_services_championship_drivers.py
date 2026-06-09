"""Unit tests for ChampionshipDriverService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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


@pytest.mark.asyncio
async def test_list_standings_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_entry()]
    client.get = AsyncMock(return_value=expected)

    service = ChampionshipDriverService(client)
    result = await service.list_standings(session_key="latest", driver_number=[1, 11])

    client.get.assert_called_once_with(
        "championship_drivers",
        ChampionshipDriver,
        session_key="latest",
        driver_number=[1, 11],
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_standings_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = ChampionshipDriverService(client)
    result = await service.list_standings()

    assert result == []
