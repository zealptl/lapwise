"""GET /v1/analysis/constructor-pitstop — constructor pit stop analytics."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.constructor_pitstop import ConstructorPitstop
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.constructor_pitstop import ConstructorPitstopService

router = APIRouter()

_DESCRIPTION = (
    "Compute pit stop performance and F1 Fantasy bracket scoring per constructor across recent "
    "race weekends.\n\n"
    "**fantasy_points_avg** — average F1 Fantasy points earned per pit stop, based on duration "
    "brackets: ≤2.0 s → 10 pts, ≤2.5 s → 7 pts, ≤3.0 s → 5 pts, otherwise 0 pts. "
    "A value above 8 indicates consistently sub-2.5 s stops.\n\n"
    "**consistency_score** — reliability metric derived from the standard deviation of stop "
    "durations (higher is more consistent). Computed as `max(0, 100 - (std_dev * 50))`; "
    "a score of 100 means every stop was identical.\n\n"
    "**sub_2s_rate** — proportion of stops completed in under 2.0 seconds; the top teams "
    "typically exceed 0.30 (30% of stops sub-2 s).\n\n"
    "**fastest_pitstop_rate** — fraction of race sessions in the sample where this constructor "
    "recorded the overall fastest individual stop.\n\n"
    "Stops longer than 60 seconds (driver holds) and null durations are excluded from all metrics. "
    "Omit `team_name` to return statistics for all constructors."
)

_200_EXAMPLE = [
    {
        "team_name": "McLaren",
        "avg_stop_duration": 2.31,
        "avg_lane_duration": 23.4,
        "fastest_stop_in_sample": 1.88,
        "fantasy_points_avg": 7.2,
        "fastest_pitstop_rate": 0.25,
        "sub_2s_rate": 0.18,
        "consistency_score": 84.5,
        "sample_stops": 28,
        "sample_races": 12,
    },
    {
        "team_name": "Red Bull Racing",
        "avg_stop_duration": 2.19,
        "avg_lane_duration": 22.1,
        "fastest_stop_in_sample": 1.82,
        "fantasy_points_avg": 8.1,
        "fastest_pitstop_rate": 0.33,
        "sub_2s_rate": 0.32,
        "consistency_score": 88.0,
        "sample_stops": 26,
        "sample_races": 12,
    },
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Pit stop performance statistics per constructor.",
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
    "/constructor-pitstop",
    operation_id="constructor_pitstop",
    response_model=list[ConstructorPitstop],
    summary="Constructor pit stop analytics",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def constructor_pitstop(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    team_name: Annotated[
        str | None,
        Query(
            description=(
                "Filter results to a single constructor by team name "
                "(e.g. `McLaren`, `Red Bull Racing`, `Ferrari`). "
                "The match is case-sensitive and must match the OpenF1 team_name exactly. "
                "Omit to return statistics for all constructors."
            )
        ),
    ] = None,
    last_n_races: Annotated[
        int,
        Query(
            description=(
                "Number of most-recent race weekends to include in the sample (minimum 1). "
                "Default 12 covers approximately one third of a full season. "
                "Higher values smooth out variance at the cost of recency."
            ),
            ge=1,
        ),
    ] = 12,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "Reserved for future circuit-scoped analysis. Currently falls back to the "
                "`last_n_races` window (no circuit context is available at this endpoint)."
            )
        ),
    ] = False,
) -> list[ConstructorPitstop]:
    """Return pit stop performance and F1 Fantasy bracket scoring per constructor."""
    service = ConstructorPitstopService(client)
    return await service.get_constructor_pitstops(team_name, last_n_races, include_circuit_history)
