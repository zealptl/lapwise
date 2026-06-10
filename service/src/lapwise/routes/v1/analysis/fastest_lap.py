"""Route handler for the fastest lap candidates analysis endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.fastest_lap import FastestLapCandidate
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.fastest_lap import FastestLapService

router = APIRouter()

_DESCRIPTION = (
    "Returns fastest lap probability metrics per driver based on historical Race and Sprint sessions.\n\n"
    "**fl_rate** — proportion of sessions in the sample where the driver set the fastest lap "
    "(e.g. 0.25 means fastest lap in 1 of every 4 races). "
    "SC-period laps are excluded using a 110% median-lap-time threshold, and all drivers "
    "sharing the minimum lap time in a session are credited.\n\n"
    "**fl_on_fresh_tyre_rate** — fraction of those fastest laps that were set on fresh tyres "
    "(low tyre age at the time of the lap); useful for predicting whether a team is likely "
    "to pit for a late fresh set.\n\n"
    "**typical_fl_position** — average finishing position in sessions where the driver set the "
    "fastest lap; a low value (e.g. 1–3) indicates the driver typically challenges from the front.\n\n"
    "When `include_circuit_history=true` and `session_key` is set, the sample is augmented with "
    "meetings at the same circuit from the previous 2 calendar years."
)

_200_EXAMPLE = [
    {
        "driver_number": 1,
        "fastest_lap_count": 4,
        "total_sessions": 12,
        "fl_rate": 0.333,
        "typical_fl_position": 1.5,
        "fl_on_fresh_tyre_rate": 0.75,
        "sample_races": 12,
    },
    {
        "driver_number": 4,
        "fastest_lap_count": 3,
        "total_sessions": 12,
        "fl_rate": 0.25,
        "typical_fl_position": 2.0,
        "fl_on_fresh_tyre_rate": 1.0,
        "sample_races": 12,
    },
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Fastest lap candidate statistics for all drivers in the sample.",
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
    "/fastest-lap-candidates",
    response_model=list[FastestLapCandidate],
    summary="Fastest lap candidates",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def fastest_lap_candidates(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
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
                "Required when `include_circuit_history=true`; ignored otherwise."
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
) -> list[FastestLapCandidate]:
    """Return fastest lap candidate statistics for all drivers in the sample."""
    service = FastestLapService(client)
    return await service.get_fastest_lap_candidates(last_n_races, session_key, include_circuit_history)
