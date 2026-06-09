"""Unit tests for WeatherService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.weather import Weather
from lapwise.services.weather import WeatherService


def _make_weather(**overrides: object) -> Weather:
    defaults: dict[str, object] = {
        "air_temperature": 27.8,
        "date": "2023-09-15T13:03:14+00:00",
        "humidity": 51.0,
        "meeting_key": 1219,
        "pressure": 1006.9,
        "rainfall": 0,
        "session_key": 9165,
        "track_temperature": 39.6,
        "wind_direction": 173,
        "wind_speed": 1.4,
    }
    defaults.update(overrides)
    return Weather(**defaults)


@pytest.mark.asyncio
async def test_list_weather_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_weather()]
    client.get = AsyncMock(return_value=expected)

    service = WeatherService(client)
    result = await service.list_weather(session_key=9165, air_temperature_gte=25.0)

    client.get.assert_called_once_with(
        "weather",
        Weather,
        session_key=9165,
        air_temperature_gte=25.0,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_weather_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = WeatherService(client)
    result = await service.list_weather()

    assert result == []
