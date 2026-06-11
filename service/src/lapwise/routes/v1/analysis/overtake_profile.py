"""Route handler for GET /v1/analysis/overtake-profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.overtake_profile import OvertakeProfile
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.overtake_profile import OvertakeProfileService

router = APIRouter()

_DESCRIPTION = (
    "Compute per-driver offensive and defensive overtake statistics from Race and Sprint sessions.\n\n"
    "**aggression_score** — percentile rank (0–100) of the driver's `overtake_rate` vs all other "
    "drivers in the same sample; 100 = most overtakes made per session. A score above 70 "
    "indicates an assertive overtaker; below 30 indicates a driver who rarely makes positions.\n\n"
    "**circuit_overtake_avg** — the driver's average overtakes per session specifically at the "
    "queried circuit. Only populated when `session_key` is provided or `include_circuit_history=true`; "
    "otherwise `null`.\n\n"
    "**total_races** is the denominator for `overtake_rate` and `defensive_rate`. Sprint weekends "
    "contribute 2 sessions (Sprint + Race) so `total_races` may exceed `sample_races`.\n\n"
    "Omitting `driver_number` returns statistics for every driver active in the sample window."
)

_200_EXAMPLE = [
    {
        "driver_number": 1,
        "overtakes_made": 18,
        "overtakes_lost": 4,
        "net_overtakes": 14,
        "overtake_rate": 1.5,
        "defensive_rate": 0.33,
        "aggression_score": 72.0,
        "circuit_overtake_avg": None,
        "sample_races": 12,
        "total_races": 14,
    },
    {
        "driver_number": 16,
        "overtakes_made": 22,
        "overtakes_lost": 8,
        "net_overtakes": 14,
        "overtake_rate": 1.57,
        "defensive_rate": 0.57,
        "aggression_score": 78.0,
        "circuit_overtake_avg": None,
        "sample_races": 12,
        "total_races": 14,
    },
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Overtake profile statistics for drivers in the sample.",
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
    "/overtake-profile",
    operation_id="overtake_profile",
    response_model=list[OvertakeProfile],
    summary="Driver overtake profiles",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def overtake_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int | None,
        Query(
            description=(
                "Filter results to a single driver by car number "
                "(e.g. 1 for Verstappen, 16 for Leclerc). "
                "Omit to return statistics for all drivers in the sample."
            )
        ),
    ] = None,
    last_n_races: Annotated[
        int,
        Query(
            description=(
                "Number of most-recent race weekends to include in the sample. "
                "Default 12 covers approximately one third of a full season. "
                "Higher values smooth out variance at the cost of recency."
            )
        ),
    ] = 12,
    session_key: Annotated[
        int | None,
        Query(
            description=(
                "OpenF1 session key used to identify the circuit. "
                "When provided, also populates `circuit_overtake_avg` for each driver. "
                "Required when `include_circuit_history=true`."
            )
        ),
    ] = None,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "When `true` and `session_key` is provided, augments the sample with "
                "meetings at the same circuit from the previous 2 calendar years, "
                "giving a larger circuit-specific dataset."
            )
        ),
    ] = False,
) -> list[OvertakeProfile]:
    """Return per-driver overtake statistics from Race and Sprint sessions."""
    service = OvertakeProfileService(client)
    return await service.get_overtake_profiles(
        driver_number, last_n_races, session_key, include_circuit_history
    )
