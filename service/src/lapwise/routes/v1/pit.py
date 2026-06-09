"""GET /v1/pit - OpenF1 pit stops wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_pit_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.pit import PitStop
from lapwise.services.pit import PitService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **pit stop** data from the OpenF1 API.\n\n"
    "Each record represents one pit stop, including the lane duration and "
    "the duration of the stationary stop.\n\n"
    "Upstream source: <https://api.openf1.org/v1/pit>\n\n"
    "Comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention "
    "(e.g. `stop_duration_lt=2.3`). `driver_number` may be repeated to filter "
    "for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "date": "2023-09-03T13:14:55.558000+00:00",
        "driver_number": 1,
        "lane_duration": 23.227,
        "lap_number": 27,
        "meeting_key": 1219,
        "pit_duration": 23.227,
        "session_key": 9165,
        "stop_duration": 2.4,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Pit stops matching the supplied filters.",
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
    "/pit",
    response_model=list[PitStop],
    summary="List pit stops",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_pit_stops(
    service: Annotated[PitService, Depends(get_pit_service)],
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
                "(e.g. `?driver_number=1&driver_number=11`)."
            )
        ),
    ] = None,
    lap_number: Annotated[
        int | None,
        Query(description="Filter by lap number."),
    ] = None,
    stop_duration_lt: Annotated[
        float | None,
        Query(description="Return pit stops with stop_duration < this value (seconds)."),
    ] = None,
    stop_duration_lte: Annotated[
        float | None,
        Query(description="Return pit stops with stop_duration <= this value (seconds)."),
    ] = None,
    stop_duration_gt: Annotated[
        float | None,
        Query(description="Return pit stops with stop_duration > this value (seconds)."),
    ] = None,
    stop_duration_gte: Annotated[
        float | None,
        Query(description="Return pit stops with stop_duration >= this value (seconds)."),
    ] = None,
) -> list[PitStop]:
    """Return pit stops matching the supplied query parameters."""
    return await service.list_pit_stops(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        lap_number=lap_number,
        stop_duration_lt=stop_duration_lt,
        stop_duration_lte=stop_duration_lte,
        stop_duration_gt=stop_duration_gt,
        stop_duration_gte=stop_duration_gte,
    )
