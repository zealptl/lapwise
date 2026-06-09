"""GET /v1/starting_grid - OpenF1 starting grid wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_starting_grid_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.services.starting_grid import StartingGridService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **starting grid** data from the OpenF1 API.\n\n"
    "Each record represents a driver's grid position for a race session, "
    "including the qualifying lap time that determined the position.\n\n"
    "Upstream source: <https://api.openf1.org/v1/starting_grid>\n\n"
    "Comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention "
    "(e.g. `position_lte=10`). `driver_number` may be repeated to filter "
    "for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "driver_number": 1,
        "lap_duration": 83.404,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9165,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Starting grid entries matching the supplied filters.",
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
    "/starting_grid",
    response_model=list[StartingGridEntry],
    summary="List starting grid entries",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_starting_grid(
    service: Annotated[StartingGridService, Depends(get_starting_grid_service)],
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
    position: Annotated[
        int | None,
        Query(description="Filter by exact grid position."),
    ] = None,
    position_lt: Annotated[
        int | None,
        Query(description="Return entries where position < this value."),
    ] = None,
    position_lte: Annotated[
        int | None,
        Query(description="Return entries where position <= this value."),
    ] = None,
    position_gt: Annotated[
        int | None,
        Query(description="Return entries where position > this value."),
    ] = None,
    position_gte: Annotated[
        int | None,
        Query(description="Return entries where position >= this value."),
    ] = None,
) -> list[StartingGridEntry]:
    """Return starting grid entries matching the supplied query parameters."""
    return await service.list_grid(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        position=position,
        position_lt=position_lt,
        position_lte=position_lte,
        position_gt=position_gt,
        position_gte=position_gte,
    )
