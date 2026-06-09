"""Unit tests for StintService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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


@pytest.mark.asyncio
async def test_list_stints_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_stint()]
    client.get = AsyncMock(return_value=expected)

    service = StintService(client)
    result = await service.list_stints(session_key=9165, tyre_age_at_start_gte=3)

    client.get.assert_called_once_with(
        "stints",
        Stint,
        session_key=9165,
        tyre_age_at_start_gte=3,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_stints_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = StintService(client)
    result = await service.list_stints()

    assert result == []
