"""Route handler for GET /v1/position."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_position_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.position import Position
from lapwise.services.position import PositionService

router = APIRouter()

_DESCRIPTION = (
    "Returns a list of driver position records for the given session.\n\n"
    "Each record captures a driver race position at a point in time."
    " Multiple records per driver reflect every position change.\n\n"
    "Upstream: <https://api.openf1.org/v1/position>\n\n"
    "Filters _lt/_lte/_gt/_gte translate to OpenF1 operator syntax."
)

_200_EX = {
    "value": [
        {
            "date": "2023-08-27T11:00:03.000Z",
            "driver_number": 1,
            "meeting_key": 1217,
            "position": 1,
            "session_key": 9149,
        }
    ]
}
_502_EX = {
    "value": {
        "detail": "OpenF1 upstream error",
        "upstream_status": 503,
        "upstream_message": "Service Unavailable",
    }
}
_504_EX = {
    "value": {
        "detail": "OpenF1 upstream error",
        "upstream_status": None,
        "upstream_message": None,
    }
}

_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"content": {"application/json": {"examples": {"default": _200_EX}}}},
    422: {"description": "Validation Error"},
    502: {
        "description": "Bad Gateway",
        "model": ErrorEnvelope,
        "content": {"application/json": {"examples": {"err": _502_EX}}},
    },
    504: {
        "description": "Gateway Timeout",
        "model": ErrorEnvelope,
        "content": {"application/json": {"examples": {"tout": _504_EX}}},
    },
}


@router.get(
    "/position",
    summary="List position records",
    description=_DESCRIPTION,
    response_model=list[Position],
    responses=_RESPONSES,
)
async def list_positions(
    session_key: Annotated[
        int | None,
        Query(description="Filter by session key."),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting key."),
    ] = None,
    driver_number: Annotated[
        list[int] | None,
        Query(description="Filter by driver number (repeat for multiple)."),
    ] = None,
    position: Annotated[
        int | None,
        Query(description="Exact position filter."),
    ] = None,
    position_lt: Annotated[
        int | None,
        Query(description="Return records where position < value."),
    ] = None,
    position_lte: Annotated[
        int | None,
        Query(description="Return records where position <= value."),
    ] = None,
    position_gt: Annotated[
        int | None,
        Query(description="Return records where position > value."),
    ] = None,
    position_gte: Annotated[
        int | None,
        Query(description="Return records where position >= value."),
    ] = None,
    service: Annotated[PositionService, Depends(get_position_service)] = None,  # type: ignore[assignment]
) -> list[Position]:
    """Return position records from OpenF1, applying optional filters."""
    return await service.list_positions(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        position=position,
        position_lt=position_lt,
        position_lte=position_lte,
        position_gt=position_gt,
        position_gte=position_gte,
    )
