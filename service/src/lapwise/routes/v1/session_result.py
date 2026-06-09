"""GET /v1/session_result - OpenF1 session results wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_session_result_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.session_result import SessionResult
from lapwise.services.session_result import SessionResultService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve final **session classification** data from the OpenF1 API.\n\n"
    "Each record represents a driver's finishing position and result for one session. "
    "For races and sprints, `duration` is a single float (seconds). "
    "For qualifying, `duration` is an array of three floats representing Q1/Q2/Q3 times.\n\n"
    "Upstream source: <https://api.openf1.org/v1/session_result>\n\n"
    "Position comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention. "
    "`driver_number` may be repeated to filter for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "dnf": False,
        "dns": False,
        "dsq": False,
        "driver_number": 1,
        "duration": [80.260, 79.840, None],
        "gap_to_leader": None,
        "number_of_laps": None,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9161,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Session results matching the supplied filters.",
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
    "/session_result",
    response_model=list[SessionResult],
    summary="List session results",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_session_results(
    service: Annotated[SessionResultService, Depends(get_session_result_service)],
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
        Query(description="Filter by exact finishing position."),
    ] = None,
    position_lt: Annotated[
        int | None,
        Query(description="Return results with position < this value."),
    ] = None,
    position_lte: Annotated[
        int | None,
        Query(description="Return results with position <= this value."),
    ] = None,
    position_gt: Annotated[
        int | None,
        Query(description="Return results with position > this value."),
    ] = None,
    position_gte: Annotated[
        int | None,
        Query(description="Return results with position >= this value."),
    ] = None,
    dnf: Annotated[
        bool | None,
        Query(description="Filter to only DNF results (true) or exclude them (false)."),
    ] = None,
    dns: Annotated[
        bool | None,
        Query(description="Filter to only DNS results (true) or exclude them (false)."),
    ] = None,
    dsq: Annotated[
        bool | None,
        Query(description="Filter to only DSQ results (true) or exclude them (false)."),
    ] = None,
) -> list[SessionResult]:
    """Return session results matching the supplied query parameters."""
    return await service.list_results(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        position=position,
        position_lt=position_lt,
        position_lte=position_lte,
        position_gt=position_gt,
        position_gte=position_gte,
        dnf=dnf,
        dns=dns,
        dsq=dsq,
    )
