"""GET /v1/championship_drivers - OpenF1 championship drivers wrapper."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_championship_driver_service
from lapwise.models.championship import ChampionshipDriver
from lapwise.models.common import ErrorEnvelope
from lapwise.services.championship import ChampionshipDriverService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **championship driver standings** from the OpenF1 API.\n\n"
    "Each record represents a driver's championship points and position before and "
    "after a specific race meeting.\n\n"
    "**Note:** This endpoint is marked *beta* by OpenF1 and only covers race sessions.\n\n"
    "Upstream source: <https://api.openf1.org/v1/championship_drivers>\n\n"
    "`session_key` and `meeting_key` accept an integer key or the special string "
    '`"latest"` to fetch the most recent available data. '
    "`driver_number` may be repeated to filter for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "driver_number": 1,
        "meeting_key": 1219,
        "points_current": 331.0,
        "points_start": 306.0,
        "position_current": 1,
        "position_start": 1,
        "session_key": 9165,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Championship driver standings matching the supplied filters.",
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
    "/championship_drivers",
    response_model=list[ChampionshipDriver],
    summary="List championship driver standings",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_championship_drivers(
    service: Annotated[ChampionshipDriverService, Depends(get_championship_driver_service)],
    session_key: Annotated[
        int | Literal["latest"] | None,
        Query(description=("Filter by session key. Pass `latest` to get the most recent session.")),
    ] = None,
    meeting_key: Annotated[
        int | Literal["latest"] | None,
        Query(description=("Filter by meeting key. Pass `latest` to get the most recent meeting.")),
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
) -> list[ChampionshipDriver]:
    """Return championship driver standings matching the supplied query parameters."""
    return await service.list_standings(
        session_key=session_key,
        meeting_key=meeting_key,
        driver_number=driver_number,
    )
