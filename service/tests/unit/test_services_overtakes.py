"""Unit tests for OvertakeService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.overtakes import Overtake
from lapwise.services.overtakes import OvertakeService


def _make_overtake(**overrides: object) -> Overtake:
    defaults: dict[str, object] = {
        "date": "2023-09-03T14:12:33+00:00",
        "meeting_key": 1219,
        "overtaken_driver_number": 4,
        "overtaking_driver_number": 63,
        "position": 3,
        "session_key": 9165,
    }
    defaults.update(overrides)
    return Overtake(**defaults)


@pytest.mark.asyncio
async def test_list_overtakes_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_overtake()]
    client.get = AsyncMock(return_value=expected)

    service = OvertakeService(client)
    result = await service.list_overtakes(
        session_key=9636,
        overtaking_driver_number=63,
        overtaken_driver_number=4,
    )

    client.get.assert_called_once_with(
        "overtakes",
        Overtake,
        session_key=9636,
        overtaking_driver_number=63,
        overtaken_driver_number=4,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_overtakes_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = OvertakeService(client)
    result = await service.list_overtakes()

    assert result == []
