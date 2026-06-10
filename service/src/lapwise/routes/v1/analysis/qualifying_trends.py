"""GET /v1/analysis/qualifying-trends — qualifying performance trends for a driver."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.qualifying_trends import QualifyingTrends
from lapwise.services.analysis.qualifying_trends import QualifyingTrendsService

router = APIRouter()


@router.get(
    "/qualifying-trends",
    response_model=QualifyingTrends,
    summary="Qualifying trends for a driver",
    description=(
        "Aggregate qualifying performance statistics for the specified driver "
        "across the most-recent race weekends.\n\n"
        "Metrics include decay-weighted average grid position, Q2/Q3 appearance "
        "rates, per-sector dominance, expected vs actual grid position, and a "
        "recent trend indicator (IMPROVING / STABLE / DECLINING)."
    ),
)
async def qualifying_trends(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[
        int,
        Query(description="Car number of the driver."),
    ],
    last_n_races: Annotated[
        int,
        Query(description="Number of most-recent race weekends to include (default 12)."),
    ] = 12,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "When true, attempt to merge same-circuit meetings from previous "
                "calendar years.  Currently a no-op for this endpoint as no circuit "
                "scope is provided."
            )
        ),
    ] = False,
) -> QualifyingTrends:
    """Return qualifying trend metrics for the given driver."""
    service = QualifyingTrendsService(client)
    return await service.get_qualifying_trends(driver_number, last_n_races, include_circuit_history)
