"""GET /v1/analysis/driver-pace-profile — driver pace profile analysis."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.driver_pace import DriverPaceProfile
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.driver_pace import DriverPaceService

logger = logging.getLogger("lapwise.routes.driver_pace")

router = APIRouter()

_DESCRIPTION = (
    "Compute a multi-dimensional pace profile for a single driver across recent race weekends.\n\n"
    "**qpace_score** — decay-weighted qualifying pace score (0–100) relative to the field; "
    "higher values indicate consistently faster qualifying laps. "
    "**qpace_trend** — direction of qualifying pace over the sample window: "
    "`IMPROVING`, `STABLE`, or `DECLINING`.\n\n"
    "**sector_1_delta / sector_2_delta / sector_3_delta** — average gap (seconds) to the "
    "field's fastest sector time in qualifying; smaller is better. "
    "**strongest_sector** — the sector where the driver's average delta is smallest "
    "(`S1`, `S2`, or `S3`).\n\n"
    "**rpace_score** — clean-air race pace score relative to the field, derived from "
    "lap times after safety car and first-lap incidents are excluded. "
    "**rpace_percentile** — percentile rank of `rpace_score` vs the full field (0–100; 100 = fastest).\n\n"
    "**overtake_adjustment** — additive pace score adjustment applied for races started from P10 "
    "or lower, rewarding strong pace despite a difficult grid position.\n\n"
    "When `include_circuit_history=true` and `session_key` is set, the sample is augmented with "
    "meetings at the same circuit from the previous 2 calendar years."
)

_200_EXAMPLE = {
    "driver_number": 1,
    "qpace_score": 87.4,
    "qpace_trend": "STABLE",
    "sector_1_delta": 0.042,
    "sector_2_delta": 0.018,
    "sector_3_delta": 0.065,
    "strongest_sector": "S2",
    "rpace_score": 91.2,
    "rpace_percentile": 96.0,
    "overtake_adjustment": 1.5,
    "sample_races": 12,
}

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Pace profile for the requested driver.",
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
    "/driver-pace-profile",
    operation_id="driver_pace_profile",
    response_model=DriverPaceProfile,
    summary="Driver pace profile",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def driver_pace_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int,
        Query(
            description=(
                "Car number of the driver to profile (e.g. 1 for Verstappen, 16 for Leclerc). "
                "Must match the official OpenF1 driver_number."
            )
        ),
    ],
    last_n_races: Annotated[
        int,
        Query(
            description=(
                "Number of most-recent race weekends to include in the sample window. "
                "Default 12 covers approximately one third of a full season. "
                "Higher values smooth out variance at the cost of recency."
            )
        ),
    ] = 12,
    session_key: Annotated[
        int | None,
        Query(
            description=(
                "OpenF1 session key used to identify the circuit for circuit-specific analysis. "
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
) -> DriverPaceProfile:
    """Return a multi-dimensional pace profile for the requested driver."""
    logger.info(
        "driver_pace_profile called driver_number=%d last_n_races=%d session_key=%s include_circuit_history=%s",
        driver_number, last_n_races, session_key, include_circuit_history,
    )
    service = DriverPaceService(client)
    result = await service.get_driver_pace_profile(
        driver_number, last_n_races, session_key, include_circuit_history
    )
    logger.info("driver_pace_profile completed sample_races=%d", result.sample_races)
    return result
