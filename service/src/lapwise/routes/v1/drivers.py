"""GET /v1/drivers - OpenF1 drivers wrapper."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_driver_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.drivers import Driver
from lapwise.services.drivers import DriverService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **drivers** from the OpenF1 API.\n\n"
    "Each record represents a driver entry for a specific session, "
    "including their car number, name, team, and headshot.\n\n"
    "Upstream source: <https://api.openf1.org/v1/drivers>\n\n"
    "All query parameters are optional and combined with AND semantics. "
    "`driver_number` may be repeated to filter for multiple drivers at once."
)

_200_EXAMPLE = [
    {
        "broadcast_name": "M VERSTAPPEN",
        "country_code": "NED",
        "driver_number": 1,
        "first_name": "Max",
        "full_name": "Max Verstappen",
        "headshot_url": "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/img/MAXVER01_Max_Verstappen.png",
        "last_name": "Verstappen",
        "meeting_key": 1216,
        "name_acronym": "VER",
        "session_key": 9140,
        "team_colour": "3671C6",
        "team_name": "Red Bull Racing",
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Drivers matching the supplied filters.",
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
    "/drivers",
    response_model=list[Driver],
    summary="List drivers",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_drivers(
    service: Annotated[DriverService, Depends(get_driver_service)],
    driver_number: Annotated[
        list[int] | None,
        Query(
            description=(
                "Filter by driver number. Repeat to include multiple drivers "
                "(e.g. `?driver_number=1&driver_number=11`)."
            )
        ),
    ] = None,
    session_key: Annotated[
        int | None,
        Query(description="Filter by session key."),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting (race weekend) key."),
    ] = None,
    team_name: Annotated[
        str | None,
        Query(description="Filter by constructor team name (e.g. Red Bull Racing)."),
    ] = None,
    country_code: Annotated[
        str | None,
        Query(description="Filter by ISO 3166-1 alpha-3 country code (e.g. NED)."),
    ] = None,
) -> list[Driver]:
    """Return drivers matching the supplied query parameters."""
    return await service.list_drivers(
        driver_number=driver_number,
        session_key=session_key,
        meeting_key=meeting_key,
        team_name=team_name,
        country_code=country_code,
    )
