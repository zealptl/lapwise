"""Unit tests for GET /v1/weather."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import respx
from fastapi.testclient import TestClient

from lapwise.main import create_app
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


def _fixture_client(mock_svc: WeatherService) -> TestClient:
    from lapwise.deps import get_weather_service

    app = create_app()
    app.dependency_overrides[get_weather_service] = lambda: mock_svc
    return TestClient(app, raise_server_exceptions=False)


def test_list_weather_returns_200() -> None:
    """GET /v1/weather returns 200."""
    mock_svc = MagicMock(spec=WeatherService)
    mock_svc.list_weather = AsyncMock(return_value=[_make_weather()])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/weather")
    assert response.status_code == 200
    assert response.json()[0]["air_temperature"] == 27.8


def test_list_weather_comparison_filter() -> None:
    """GET /v1/weather?air_temperature_gte=25 forwards comparison filter."""
    mock_svc = MagicMock(spec=WeatherService)
    mock_svc.list_weather = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/weather?session_key=9165&air_temperature_gte=25")
    assert response.status_code == 200
    assert mock_svc.list_weather.call_args.kwargs.get("air_temperature_gte") == 25.0


def test_list_weather_multiple_comparison_filters() -> None:
    """GET /v1/weather forwards multiple _gte filters together."""
    mock_svc = MagicMock(spec=WeatherService)
    mock_svc.list_weather = AsyncMock(return_value=[])
    client = _fixture_client(mock_svc)
    response = client.get("/v1/weather?air_temperature_gte=25&track_temperature_lte=50")
    assert response.status_code == 200
    kwargs = mock_svc.list_weather.call_args.kwargs
    assert kwargs.get("air_temperature_gte") == 25.0
    assert kwargs.get("track_temperature_lte") == 50.0


@respx.mock
def test_list_weather_upstream_502() -> None:
    """GET /v1/weather returns 502 when OpenF1 returns 503."""
    respx.get("https://api.openf1.org/v1/weather").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/v1/weather")
    assert response.status_code == 502
