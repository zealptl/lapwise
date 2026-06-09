"""GET /v1/overtakes - OpenF1 overtakes wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_overtake_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.overtakes import Overtake
from lapwise.services.overtakes import OvertakeService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **overtake events** from the OpenF1 API.\n\n"
    "Each record represents one driver overtaking another at a specific track position.\n\n"
    "**Note:** This data is only available for race sessions and may be incomplete — "
    "not all overtakes are captured.\n\n"
    "Upstream source: <https://api.openf1.org/v1/overtakes>"
)

_200_EXAMPLE = [
    {
        "date": "2023-09-03T14:12:33.765000+00:00",
        "meeting_key": 1219,
        "overtaken_driver_number": 4,
        "overtaking_driver_number": 63,
        "position": 3,
        "session_key": 9165,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Overtakes matching the supplied filters.",
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
    "/overtakes",
    response_model=list[Overtake],
    summary="List overtakes",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_overtakes(
    service: Annotated[OvertakeService, Depends(get_overtake_service)],
    session_key: Annotated[
        int | None,
        Query(description="Filter by session key."),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting (race weekend) key."),
    ] = None,
    overtaking_driver_number: Annotated[
        int | None,
        Query(description="Filter by the driver number of the overtaking driver."),
    ] = None,
    overtaken_driver_number: Annotated[
        int | None,
        Query(description="Filter by the driver number of the driver who was overtaken."),
    ] = None,
    position: Annotated[
        int | None,
        Query(description="Filter by track position where the overtake occurred."),
    ] = None,
) -> list[Overtake]:
    """Return overtakes matching the supplied query parameters."""
    return await service.list_overtakes(
        session_key=session_key,
        meeting_key=meeting_key,
        overtaking_driver_number=overtaking_driver_number,
        overtaken_driver_number=overtaken_driver_number,
        position=position,
    )
