"""Unit tests for LapService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.laps import Lap
from lapwise.services.laps import LapService


def _make_lap(**overrides: object) -> Lap:
    defaults: dict[str, object] = {
        "date_start": None,
        "driver_number": 1,
        "duration_sector_1": 26.966,
        "duration_sector_2": 38.657,
        "duration_sector_3": 26.14,
        "i1_speed": 307,
        "i2_speed": 277,
        "is_pit_out_lap": False,
        "lap_duration": 91.763,
        "lap_number": 8,
        "meeting_key": 1219,
        "segments_sector_1": None,
        "segments_sector_2": None,
        "segments_sector_3": None,
        "session_key": 9161,
        "st_speed": 298,
    }
    defaults.update(overrides)
    return Lap(**defaults)


@pytest.mark.asyncio
async def test_list_laps_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_lap()]
    client.get = AsyncMock(return_value=expected)

    service = LapService(client)
    result = await service.list_laps(session_key=9161, driver_number=63, lap_number=8)

    client.get.assert_called_once_with(
        "laps",
        Lap,
        session_key=9161,
        driver_number=63,
        lap_number=8,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_laps_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = LapService(client)
    result = await service.list_laps()

    assert result == []
