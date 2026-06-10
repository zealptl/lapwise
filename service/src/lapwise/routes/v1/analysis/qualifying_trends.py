"""GET /v1/analysis/qualifying-trends — qualifying performance trends for a driver."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.qualifying_trends import QualifyingTrends
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.qualifying_trends import QualifyingTrendsService

router = APIRouter()

_DESCRIPTION = (
    "Aggregate qualifying performance statistics for the specified driver across the most-recent "
    "race weekends.\n\n"
    "**q3_appearance_rate** — fraction of sessions where the driver started from positions 1–10, "
    "used as a proxy for reaching Q3 (direct Q3 session data is not always available). "
    "A value of 1.0 means the driver qualified in the top 10 in every sampled session.\n\n"
    "**sector_dominance** — per-sector breakdown of `avg_delta_to_fastest` (seconds gap to "
    "the field's best sector time) and `dominance_rate` (fraction of sessions where the driver "
    "set the overall fastest sector time). Use `strongest_sector` for a quick read on where "
    "the driver gains the most time.\n\n"
    "**grid_vs_expected** — average difference between actual grid position and the driver's "
    "championship position at the time of the race. Negative values mean the driver qualifies "
    "ahead of their standing; positive means they underperform their championship rank.\n\n"
    "**recent_trend** — direction of grid position over the sample: `IMPROVING`, `STABLE`, or "
    "`DECLINING`. Computed by comparing the decay-weighted average of the older half of sessions "
    "against the newer half (threshold ±10%)."
)

_200_EXAMPLE = {
    "driver_number": 4,
    "sessions_analysed": 12,
    "avg_grid_position": 2.8,
    "best_grid_position": 1,
    "worst_grid_position": 6,
    "q3_appearance_rate": 1.0,
    "q2_appearance_rate": 1.0,
    "sector_dominance": {
        "sector_1": {"avg_delta_to_fastest": 0.038, "dominance_rate": 0.25},
        "sector_2": {"avg_delta_to_fastest": 0.012, "dominance_rate": 0.42},
        "sector_3": {"avg_delta_to_fastest": 0.055, "dominance_rate": 0.17},
    },
    "strongest_sector": 2,
    "grid_vs_expected": -0.3,
    "recent_trend": "IMPROVING",
}

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Qualifying trend metrics for the requested driver.",
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
    "/qualifying-trends",
    response_model=QualifyingTrends,
    summary="Qualifying trends for a driver",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def qualifying_trends(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int,
        Query(
            description=(
                "Car number of the driver to analyse "
                "(e.g. 4 for Norris, 16 for Leclerc). "
                "Must match the official OpenF1 driver_number."
            )
        ),
    ],
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
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "Reserved for future circuit-scoped analysis. Currently a no-op — "
                "no circuit context is available at this endpoint, so the full "
                "`last_n_races` window is always used."
            )
        ),
    ] = False,
) -> QualifyingTrends:
    """Return qualifying trend metrics for the given driver."""
    service = QualifyingTrendsService(client)
    return await service.get_qualifying_trends(driver_number, last_n_races, include_circuit_history)
