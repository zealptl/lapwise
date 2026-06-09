"""Unit tests for MeetingService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.meetings import Meeting
from lapwise.services.meetings import MeetingService


def _make_meeting(**overrides: object) -> Meeting:
    defaults: dict[str, object] = {
        "circuit_key": 16,
        "circuit_info_url": None,
        "circuit_image": None,
        "circuit_short_name": "Monza",
        "circuit_type": "permanent",
        "country_code": "ITA",
        "country_flag": None,
        "country_key": 13,
        "country_name": "Italy",
        "date_end": None,
        "date_start": None,
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Monza",
        "meeting_key": 1219,
        "meeting_name": "Italian Grand Prix",
        "meeting_official_name": None,
        "year": 2023,
    }
    defaults.update(overrides)
    return Meeting(**defaults)


@pytest.mark.asyncio
async def test_list_meetings_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_meeting()]
    client.get = AsyncMock(return_value=expected)

    service = MeetingService(client)
    result = await service.list_meetings(year=2023, country_name="Italy")

    client.get.assert_called_once_with(
        "meetings",
        Meeting,
        year=2023,
        country_name="Italy",
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_meetings_forwards_latest_literal() -> None:
    """Service forwards meeting_key='latest' unchanged to the client."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = MeetingService(client)
    await service.list_meetings(meeting_key="latest")

    client.get.assert_called_once_with("meetings", Meeting, meeting_key="latest")


@pytest.mark.asyncio
async def test_list_meetings_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = MeetingService(client)
    result = await service.list_meetings()

    assert result == []
