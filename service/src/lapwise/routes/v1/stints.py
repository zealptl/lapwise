"""GET /v1/stints - OpenF1 tyre stints wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_stint_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.stints import Stint
from lapwise.services.stints import StintService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **tyre stint** data from the OpenF1 API.\n\n"
    "Each record represents one stint — a continuous period on a set of tyres — "
    "with information about the compound and stint start/end laps.\n\n"
    "Upstream source: <https://api.openf1.org/v1/stints>\n\n"
    "Comparison filters use the `_lt`/`_lte`/`_gt`/`_gte` suffix convention "
    "(e.g. `tyre_age_at_start_gte=3`). `driver_number` may be repeated to filter "
    "for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "compound": "SOFT",
        "driver_number": 1,
        "lap_end": 27,
        "lap_start": 1,
        "meeting_key": 1219,
        "session_key": 9165,
        "stint_number": 1,
        "tyre_age_at_start": 0,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Stints matching the supplied filters.",
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
    "/stints",
    response_model=list[Stint],
    summary="List tyre stints",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_stints(
    service: Annotated[StintService, Depends(get_stint_service)],
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
    stint_number: Annotated[
        int | None,
        Query(description="Filter by stint number."),
    ] = None,
    compound: Annotated[
        str | None,
        Query(description="Filter by tyre compound (e.g. SOFT, MEDIUM, HARD)."),
    ] = None,
    tyre_age_at_start: Annotated[
        int | None,
        Query(description="Filter by exact tyre age at the start of the stint (laps)."),
    ] = None,
    tyre_age_at_start_lt: Annotated[
        int | None,
        Query(description="Return stints where tyre_age_at_start < this value."),
    ] = None,
    tyre_age_at_start_lte: Annotated[
        int | None,
        Query(description="Return stints where tyre_age_at_start <= this value."),
    ] = None,
    tyre_age_at_start_gt: Annotated[
        int | None,
        Query(description="Return stints where tyre_age_at_start > this value."),
    ] = None,
    tyre_age_at_start_gte: Annotated[
        int | None,
        Query(description="Return stints where tyre_age_at_start >= this value."),
    ] = None,
) -> list[Stint]:
    """Return stints matching the supplied query parameters."""
    return await service.list_stints(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
        stint_number=stint_number,
        compound=compound,
        tyre_age_at_start=tyre_age_at_start,
        tyre_age_at_start_lt=tyre_age_at_start_lt,
        tyre_age_at_start_lte=tyre_age_at_start_lte,
        tyre_age_at_start_gt=tyre_age_at_start_gt,
        tyre_age_at_start_gte=tyre_age_at_start_gte,
    )
