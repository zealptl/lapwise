"""Unit tests for DriverService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.drivers import Driver
from lapwise.services.drivers import DriverService


def _make_driver(**overrides: object) -> Driver:
    defaults: dict[str, object] = {
        "broadcast_name": "M VERSTAPPEN",
        "country_code": "NED",
        "driver_number": 1,
        "first_name": "Max",
        "full_name": "Max Verstappen",
        "headshot_url": None,
        "last_name": "Verstappen",
        "meeting_key": 1216,
        "name_acronym": "VER",
        "session_key": 9140,
        "team_colour": "3671C6",
        "team_name": "Red Bull Racing",
    }
    defaults.update(overrides)
    return Driver(**defaults)


@pytest.mark.asyncio
async def test_list_drivers_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_driver()]
    client.get = AsyncMock(return_value=expected)

    service = DriverService(client)
    result = await service.list_drivers(driver_number=1, session_key=9140)

    client.get.assert_called_once_with(
        "drivers",
        Driver,
        driver_number=1,
        session_key=9140,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_drivers_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = DriverService(client)
    result = await service.list_drivers()

    assert result == []
