"""Unit tests for StartingGridService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.starting_grid import StartingGridEntry
from lapwise.services.starting_grid import StartingGridService


def _make_entry(**overrides: object) -> StartingGridEntry:
    defaults: dict[str, object] = {
        "driver_number": 1,
        "lap_duration": 83.404,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9165,
    }
    defaults.update(overrides)
    return StartingGridEntry(**defaults)


@pytest.mark.asyncio
async def test_list_grid_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_entry()]
    client.get = AsyncMock(return_value=expected)

    service = StartingGridService(client)
    result = await service.list_grid(session_key=9165, position_lte=10)

    client.get.assert_called_once_with(
        "starting_grid",
        StartingGridEntry,
        session_key=9165,
        position_lte=10,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_grid_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = StartingGridService(client)
    result = await service.list_grid()

    assert result == []
