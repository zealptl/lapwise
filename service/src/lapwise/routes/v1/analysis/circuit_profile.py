"""GET /v1/analysis/circuit-profile — circuit characteristics derived from race data."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.circuit_profile import CircuitProfile
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.circuit_profile import CircuitProfileService

router = APIRouter()

_DESCRIPTION = (
    "Compute a high-level characteristics profile for an F1 circuit from historical race data.\n\n"
    "**overtake_difficulty** — categorical difficulty of overtaking: `HIGH` (fewer than 15 avg "
    "overtakes/race), `MEDIUM` (15–30), or `LOW` (more than 30). Circuits like Monaco score `HIGH`; "
    "high-speed, long-straight venues score `LOW`.\n\n"
    "**qualifying_importance** — estimated importance of grid position on race outcome (0–100), "
    "derived from `overtake_difficulty`: `HIGH`→100, `MEDIUM`→67, `LOW`→33. A high value means "
    "overtaking is rare and starting position is decisive.\n\n"
    "**safety_car_tendency** — tendency for SC periods based on the fraction of laps where at "
    "least one car exceeded 110% of the session median lap time: `HIGH` (>15%), `MEDIUM` (5–15%), "
    "or `LOW` (<5%).\n\n"
    "**weather_variability** — variability of conditions based on the fraction of weather records "
    "showing rainfall: `HIGH` (>30%), `MEDIUM` (10–30%), or `LOW` (<10%). Spa and Silverstone "
    "typically score `HIGH`.\n\n"
    "**typical_compounds** — tyre compounds used at this circuit ordered by frequency "
    "(e.g. `[\"SOFT\", \"MEDIUM\", \"HARD\"]`).\n\n"
    "All derived fields are `null` when fewer than 2 race sessions are available in the window."
)

_200_EXAMPLE = {
    "circuit_key": 6,
    "circuit_short_name": "Monaco",
    "sample_years": 3,
    "race_sessions_found": 3,
    "overtake_difficulty": "HIGH",
    "avg_overtakes_per_race": 8.3,
    "qualifying_importance": 100,
    "safety_car_tendency": "HIGH",
    "weather_variability": "MEDIUM",
    "typical_compounds": ["SOFT", "MEDIUM", "HARD"],
    "fl_typical_lap": 68.2,
    "avg_pit_stops": 1.9,
}

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Circuit profile for the requested circuit.",
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
    "/circuit-profile",
    response_model=CircuitProfile,
    summary="Circuit profile",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def circuit_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    circuit_key: Annotated[
        int,
        Query(
            description=(
                "OpenF1 circuit identifier. Use the `circuit_key` field from the "
                "/v1/meetings or /v1/sessions response to obtain the correct value "
                "(e.g. 6 for Monaco, 16 for Monza)."
            )
        ),
    ],
    last_n_years: Annotated[
        int,
        Query(
            description=(
                "Number of calendar years to include in the analysis window (minimum 1). "
                "Default 3 typically yields 3 race sessions per circuit. "
                "Increase to 5+ for circuits with limited recent data."
            ),
            ge=1,
        ),
    ] = 3,
) -> CircuitProfile:
    """Return a CircuitProfile for the requested circuit."""
    service = CircuitProfileService(client)
    return await service.get_circuit_profile(circuit_key, last_n_years)
