"""Unit tests for PitService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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


@pytest.mark.asyncio
async def test_list_pit_stops_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_pit()]
    client.get = AsyncMock(return_value=expected)

    service = PitService(client)
    result = await service.list_pit_stops(session_key=9877, stop_duration_lt=2.3)

    client.get.assert_called_once_with(
        "pit",
        PitStop,
        session_key=9877,
        stop_duration_lt=2.3,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_pit_stops_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = PitService(client)
    result = await service.list_pit_stops()

    assert result == []
