"""GET /v1/laps - OpenF1 laps wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_lap_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.laps import Lap
from lapwise.services.laps import LapService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **lap times** from the OpenF1 API.\n\n"
    "Each record represents one lap completed by a driver, including sector times, "
    "speed-trap readings, and mini-sector colour codes.\n\n"
    "Upstream source: <https://api.openf1.org/v1/laps>\n\n"
    "Comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention "
    "(e.g. `lap_duration_lt=92.0`). `driver_number` may be repeated to filter "
    "for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "date_start": "2023-09-15T13:03:35.200000+00:00",
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
        "segments_sector_1": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
        "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
        "segments_sector_3": [2048, 2048, 2048, 2048, 2048, 2048, 2048, 2048],
        "session_key": 9161,
        "st_speed": 298,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Laps matching the supplied filters.",
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
    "/laps",
    response_model=list[Lap],
    summary="List laps",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_laps(
    service: Annotated[LapService, Depends(get_lap_service)],
    session_key: Annotated[
        int | None,
        Query(description="Filter by session key."),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting (race weekend) key."),
    ] = None,
    driver_number: Annotated[
        list[int] | None,
        Query(
            description=(
                "Filter by driver number. Repeat to include multiple drivers "
                "(e.g. `?driver_number=63&driver_number=44`)."
            )
        ),
    ] = None,
    lap_number: Annotated[
        int | None,
        Query(description="Filter by lap number."),
    ] = None,
    is_pit_out_lap: Annotated[
        bool | None,
        Query(description="Filter to only pit-out laps (true) or only normal laps (false)."),
    ] = None,
    lap_duration_lt: Annotated[
        float | None,
        Query(description="Return laps with lap_duration < this value (seconds)."),
    ] = None,
    lap_duration_lte: Annotated[
        float | None,
        Query(description="Return laps with lap_duration <= this value (seconds)."),
    ] = None,
    lap_duration_gt: Annotated[
        float | None,
        Query(description="Return laps with lap_duration > this value (seconds)."),
    ] = None,
    lap_duration_gte: Annotated[
        float | None,
        Query(description="Return laps with lap_duration >= this value (seconds)."),
    ] = None,
) -> list[Lap]:
    """Return laps matching the supplied query parameters."""
    return await service.list_laps(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        lap_number=lap_number,
        is_pit_out_lap=is_pit_out_lap,
        lap_duration_lt=lap_duration_lt,
        lap_duration_lte=lap_duration_lte,
        lap_duration_gt=lap_duration_gt,
        lap_duration_gte=lap_duration_gte,
    )
