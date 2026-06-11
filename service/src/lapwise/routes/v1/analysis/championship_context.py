"""GET /v1/analysis/championship-context — Championship context endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.championship_context import ChampionshipContext
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.championship_context import ChampionshipContextService

router = APIRouter()

_DESCRIPTION = (
    "Returns a computed championship context snapshot for a given season, covering all drivers "
    "and constructors ordered by standing position.\n\n"
    "**momentum** — direction of a driver's recent scoring relative to their season average: "
    "`POSITIVE` (recent races above average), `NEUTRAL` (within ±10%), or `NEGATIVE` "
    "(recent races below average). Useful for identifying in-form drivers.\n\n"
    "**desperation_index** — urgency-to-score metric (0–100) based on the driver's points "
    "gap to the leader scaled against remaining races; 100 indicates a driver who must "
    "win every remaining race to close the gap.\n\n"
    "**constructor_battle** (driver) / **under_pressure** (constructor) — `true` when "
    "the team is within 30 points of an adjacent championship position, indicating a "
    "tight battle that may influence driver strategy.\n\n"
    "Use `after_round` to snapshot standings as of a specific meeting — only races with "
    "`meeting_key ≤ after_round` are included. Omit for the current season standings."
)

_200_EXAMPLE = {
    "season": 2025,
    "drivers": [
        {
            "driver_number": 4,
            "full_name": "Lando Norris",
            "team_name": "McLaren",
            "points_current": 198.0,
            "championship_position": 1,
            "points_gap_to_leader": 0.0,
            "points_gap_to_p3": -47.0,
            "momentum": "POSITIVE",
            "desperation_index": 0.0,
            "constructor_battle": False,
        },
        {
            "driver_number": 1,
            "full_name": "Max Verstappen",
            "team_name": "Red Bull Racing",
            "points_current": 169.0,
            "championship_position": 2,
            "points_gap_to_leader": 29.0,
            "points_gap_to_p3": -22.0,
            "momentum": "NEUTRAL",
            "desperation_index": 38.5,
            "constructor_battle": True,
        },
    ],
    "constructors": [
        {
            "team_name": "McLaren",
            "points_current": 391.0,
            "constructor_position": 1,
            "points_gap_to_leader": 0.0,
            "under_pressure": False,
        },
        {
            "team_name": "Ferrari",
            "points_current": 344.0,
            "constructor_position": 2,
            "points_gap_to_leader": 47.0,
            "under_pressure": False,
        },
    ],
}

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Championship context snapshot for the requested season.",
        "content": {"application/json": {"example": _200_EXAMPLE}},
    },
    422: {
        "description": "Validation error — one or more query parameters are invalid.",
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
    "/championship-context",
    operation_id="championship_context",
    response_model=ChampionshipContext,
    summary="Championship context snapshot",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def championship_context(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    season: Annotated[
        int | None,
        Query(
            description=(
                "Championship year to analyse (e.g. 2025). "
                "Defaults to the current calendar year when omitted."
            )
        ),
    ] = None,
    after_round: Annotated[
        int | None,
        Query(
            description=(
                "Snapshot standings after this `meeting_key`. "
                "Only meetings with `meeting_key ≤ after_round` are included in the calculation. "
                "Omit to use all available results for the season."
            )
        ),
    ] = None,
) -> ChampionshipContext:
    """Return a full championship context snapshot for drivers and constructors."""
    service = ChampionshipContextService(client)
    return await service.get_championship_context(season, after_round)
