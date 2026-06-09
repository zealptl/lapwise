"""GET /v1/weather - OpenF1 weather wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_weather_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.weather import Weather
from lapwise.services.weather import WeatherService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **weather** data from the OpenF1 API.\n\n"
    "Each record is a weather sample captured during a session, "
    "including air/track temperature, humidity, pressure, wind, and rainfall.\n\n"
    "Upstream source: <https://api.openf1.org/v1/weather>\n\n"
    "Comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention "
    "(e.g. `air_temperature_gte=30`)."
)

_200_EXAMPLE = [
    {
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
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Weather samples matching the supplied filters.",
        "content": {"application/json": {"example": _200_EXAMPLE}},
    },
    422: {
        "description": "Validation error - one or more query parameters are invalid.",
        "model": ErrorEnvelope,
    },
    502: {
        "description": "Bad Gateway - OpenF1 returned an unexpected error.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "OpenF1 upstream error",
                    "upstream_status": 503,
                    "upstream_message": "Service Unavailable",
                }
            }
        },
    },
    504: {
        "description": "Gateway Timeout - OpenF1 did not respond in time.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "OpenF1 upstream error",
                    "upstream_status": None,
                    "upstream_message": None,
                }
            }
        },
    },
}


@router.get(
    "/weather",
    response_model=list[Weather],
    summary="List weather samples",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_weather(
    service: Annotated[WeatherService, Depends(get_weather_service)],
    session_key: Annotated[
        int | None,
        Query(description="Filter by session key."),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting (race weekend) key."),
    ] = None,
    air_temperature: Annotated[
        float | None,
        Query(description="Filter by exact air temperature (°C)."),
    ] = None,
    air_temperature_lt: Annotated[
        float | None,
        Query(description="Return samples where air_temperature < this value."),
    ] = None,
    air_temperature_lte: Annotated[
        float | None,
        Query(description="Return samples where air_temperature <= this value."),
    ] = None,
    air_temperature_gt: Annotated[
        float | None,
        Query(description="Return samples where air_temperature > this value."),
    ] = None,
    air_temperature_gte: Annotated[
        float | None,
        Query(description="Return samples where air_temperature >= this value."),
    ] = None,
    track_temperature: Annotated[
        float | None,
        Query(description="Filter by exact track surface temperature (°C)."),
    ] = None,
    track_temperature_lt: Annotated[
        float | None,
        Query(description="Return samples where track_temperature < this value."),
    ] = None,
    track_temperature_lte: Annotated[
        float | None,
        Query(description="Return samples where track_temperature <= this value."),
    ] = None,
    track_temperature_gt: Annotated[
        float | None,
        Query(description="Return samples where track_temperature > this value."),
    ] = None,
    track_temperature_gte: Annotated[
        float | None,
        Query(description="Return samples where track_temperature >= this value."),
    ] = None,
    humidity: Annotated[
        float | None,
        Query(description="Filter by exact humidity (%)."),
    ] = None,
    humidity_lt: Annotated[
        float | None,
        Query(description="Return samples where humidity < this value."),
    ] = None,
    humidity_lte: Annotated[
        float | None,
        Query(description="Return samples where humidity <= this value."),
    ] = None,
    humidity_gt: Annotated[
        float | None,
        Query(description="Return samples where humidity > this value."),
    ] = None,
    humidity_gte: Annotated[
        float | None,
        Query(description="Return samples where humidity >= this value."),
    ] = None,
    pressure: Annotated[
        float | None,
        Query(description="Filter by exact atmospheric pressure (mbar)."),
    ] = None,
    pressure_lt: Annotated[
        float | None,
        Query(description="Return samples where pressure < this value."),
    ] = None,
    pressure_lte: Annotated[
        float | None,
        Query(description="Return samples where pressure <= this value."),
    ] = None,
    pressure_gt: Annotated[
        float | None,
        Query(description="Return samples where pressure > this value."),
    ] = None,
    pressure_gte: Annotated[
        float | None,
        Query(description="Return samples where pressure >= this value."),
    ] = None,
    rainfall: Annotated[
        int | None,
        Query(description="Filter by rainfall indicator (0 = dry, 1 = wet)."),
    ] = None,
    rainfall_lt: Annotated[
        int | None,
        Query(description="Return samples where rainfall < this value."),
    ] = None,
    rainfall_lte: Annotated[
        int | None,
        Query(description="Return samples where rainfall <= this value."),
    ] = None,
    rainfall_gt: Annotated[
        int | None,
        Query(description="Return samples where rainfall > this value."),
    ] = None,
    rainfall_gte: Annotated[
        int | None,
        Query(description="Return samples where rainfall >= this value."),
    ] = None,
    wind_speed: Annotated[
        float | None,
        Query(description="Filter by exact wind speed (m/s)."),
    ] = None,
    wind_speed_lt: Annotated[
        float | None,
        Query(description="Return samples where wind_speed < this value."),
    ] = None,
    wind_speed_lte: Annotated[
        float | None,
        Query(description="Return samples where wind_speed <= this value."),
    ] = None,
    wind_speed_gt: Annotated[
        float | None,
        Query(description="Return samples where wind_speed > this value."),
    ] = None,
    wind_speed_gte: Annotated[
        float | None,
        Query(description="Return samples where wind_speed >= this value."),
    ] = None,
    wind_direction: Annotated[
        int | None,
        Query(description="Filter by exact wind direction (degrees)."),
    ] = None,
    wind_direction_lt: Annotated[
        int | None,
        Query(description="Return samples where wind_direction < this value."),
    ] = None,
    wind_direction_lte: Annotated[
        int | None,
        Query(description="Return samples where wind_direction <= this value."),
    ] = None,
    wind_direction_gt: Annotated[
        int | None,
        Query(description="Return samples where wind_direction > this value."),
    ] = None,
    wind_direction_gte: Annotated[
        int | None,
        Query(description="Return samples where wind_direction >= this value."),
    ] = None,
) -> list[Weather]:
    """Return weather samples matching the supplied query parameters."""
    return await service.list_weather(
        session_key=session_key,
        meeting_key=meeting_key,
        air_temperature=air_temperature,
        air_temperature_lt=air_temperature_lt,
        air_temperature_lte=air_temperature_lte,
        air_temperature_gt=air_temperature_gt,
        air_temperature_gte=air_temperature_gte,
        track_temperature=track_temperature,
        track_temperature_lt=track_temperature_lt,
        track_temperature_lte=track_temperature_lte,
        track_temperature_gt=track_temperature_gt,
        track_temperature_gte=track_temperature_gte,
        humidity=humidity,
        humidity_lt=humidity_lt,
        humidity_lte=humidity_lte,
        humidity_gt=humidity_gt,
        humidity_gte=humidity_gte,
        pressure=pressure,
        pressure_lt=pressure_lt,
        pressure_lte=pressure_lte,
        pressure_gt=pressure_gt,
        pressure_gte=pressure_gte,
        rainfall=rainfall,
        rainfall_lt=rainfall_lt,
        rainfall_lte=rainfall_lte,
        rainfall_gt=rainfall_gt,
        rainfall_gte=rainfall_gte,
        wind_speed=wind_speed,
        wind_speed_lt=wind_speed_lt,
        wind_speed_lte=wind_speed_lte,
        wind_speed_gt=wind_speed_gt,
        wind_speed_gte=wind_speed_gte,
        wind_direction=wind_direction,
        wind_direction_lt=wind_direction_lt,
        wind_direction_lte=wind_direction_lte,
        wind_direction_gt=wind_direction_gt,
        wind_direction_gte=wind_direction_gte,
    )
