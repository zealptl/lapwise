"""GET /v1/analysis/dnf-rates — driver DNF/DNS/DSQ rate analysis."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.dnf_rates import DnfRates
from lapwise.services.analysis.dnf_rates import DnfRatesService

router = APIRouter()


@router.get("/dnf-rates", response_model=list[DnfRates])
async def dnf_rates(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int | None,
        Query(description="Filter results to a single driver by car number."),
    ] = None,
    season: Annotated[
        int | None,
        Query(description="Championship year to restrict meetings to (e.g. 2024)."),
    ] = None,
    last_n_races: Annotated[
        int,
        Query(description="Number of most-recent race weekends to include in the sample."),
    ] = 12,
) -> list[DnfRates]:
    """Return DNF/DNS/DSQ rates for drivers across recent competitive sessions."""
    service = DnfRatesService(client)
    return await service.get_dnf_rates(driver_number, season, last_n_races)
