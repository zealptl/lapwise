"""GET /v1/championship_teams - OpenF1 championship teams wrapper."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_championship_team_service
from lapwise.models.championship import ChampionshipTeam
from lapwise.models.common import ErrorEnvelope
from lapwise.services.championship import ChampionshipTeamService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **championship team (constructor) standings** from the OpenF1 API.\n\n"
    "Each record represents a constructor's championship points and position before and "
    "after a specific race meeting.\n\n"
    "**Note:** This endpoint is marked *beta* by OpenF1 and only covers race sessions.\n\n"
    "Upstream source: <https://api.openf1.org/v1/championship_teams>\n\n"
    "`session_key` and `meeting_key` accept an integer key or the special string "
    '`"latest"` to fetch the most recent available data.'
)

_200_EXAMPLE = [
    {
        "meeting_key": 1219,
        "points_current": 860.0,
        "points_start": 835.0,
        "position_current": 1,
        "position_start": 1,
        "session_key": 9165,
        "team_name": "Red Bull Racing",
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Championship team standings matching the supplied filters.",
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
    "/championship_teams",
    response_model=list[ChampionshipTeam],
    summary="List championship team standings",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_championship_teams(
    service: Annotated[ChampionshipTeamService, Depends(get_championship_team_service)],
    session_key: Annotated[
        int | Literal["latest"] | None,
        Query(description="Filter by session key. Pass `latest` to get the most recent session."),
    ] = None,
    meeting_key: Annotated[
        int | Literal["latest"] | None,
        Query(description="Filter by meeting key. Pass `latest` to get the most recent meeting."),
    ] = None,
    team_name: Annotated[
        str | None,
        Query(description="Filter by constructor/team name (e.g. Red Bull Racing)."),
    ] = None,
) -> list[ChampionshipTeam]:
    """Return championship team standings matching the supplied query parameters."""
    return await service.list_standings(
        session_key=session_key,
        meeting_key=meeting_key,
        team_name=team_name,
    )
