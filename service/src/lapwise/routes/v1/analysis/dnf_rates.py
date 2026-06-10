"""GET /v1/analysis/dnf-rates — driver DNF/DNS/DSQ rate analysis."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.dnf_rates import DnfRates
from lapwise.models.common import ErrorEnvelope
from lapwise.services.analysis.dnf_rates import DnfRatesService

router = APIRouter()

_DESCRIPTION = (
    "Analyse driver reliability by computing DNF, DNS, and DSQ rates across recent competitive sessions.\n\n"
    "**reliability_score** — composite score (0–100) inversely proportional to the overall "
    "non-finish rate; a score of 100 means zero retirements in the sample, while lower values "
    "reflect increasing unreliability. The score is computed as "
    "`max(0, 100 * (1 - dnf_rate))`.\n\n"
    "**breakdown** — splits the overall rate into `qualifying_dnf_rate`, `race_dnf_rate`, and "
    "`sprint_dnf_rate` so you can identify whether issues cluster in a specific session type.\n\n"
    "`total_sessions` counts all qualifying, race, and sprint sessions in the sample. "
    "Omitting `driver_number` returns statistics for every driver found in the window."
)

_200_EXAMPLE = [
    {
        "driver_number": 1,
        "dnf_count": 1,
        "dns_count": 0,
        "dsq_count": 0,
        "total_sessions": 36,
        "dnf_rate": 0.028,
        "reliability_score": 97.2,
        "breakdown": {
            "qualifying_dnf_rate": 0.0,
            "race_dnf_rate": 0.083,
            "sprint_dnf_rate": 0.0,
        },
        "sample_races": 12,
    },
    {
        "driver_number": 16,
        "dnf_count": 3,
        "dns_count": 0,
        "dsq_count": 0,
        "total_sessions": 36,
        "dnf_rate": 0.083,
        "reliability_score": 91.7,
        "breakdown": {
            "qualifying_dnf_rate": 0.083,
            "race_dnf_rate": 0.083,
            "sprint_dnf_rate": 0.0,
        },
        "sample_races": 12,
    },
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "DNF/DNS/DSQ rates for drivers in the sample.",
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
    "/dnf-rates",
    response_model=list[DnfRates],
    summary="Driver DNF rates",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def dnf_rates(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int | None,
        Query(
            description=(
                "Filter results to a single driver by car number "
                "(e.g. 1 for Verstappen, 44 for Hamilton). "
                "Omit to return statistics for all drivers in the sample."
            )
        ),
    ] = None,
    season: Annotated[
        int | None,
        Query(
            description=(
                "Championship year to restrict meetings to (e.g. 2024). "
                "When omitted the sample spans the most-recent `last_n_races` race weekends "
                "regardless of season."
            )
        ),
    ] = None,
    last_n_races: Annotated[
        int,
        Query(
            description=(
                "Number of most-recent race weekends to include in the sample. "
                "Default 12 covers approximately one third of a full season. "
                "Ignored when `season` is supplied — in that case all rounds in the "
                "season are used."
            )
        ),
    ] = 12,
) -> list[DnfRates]:
    """Return DNF/DNS/DSQ rates for drivers across recent competitive sessions."""
    service = DnfRatesService(client)
    return await service.get_dnf_rates(driver_number, season, last_n_races)
