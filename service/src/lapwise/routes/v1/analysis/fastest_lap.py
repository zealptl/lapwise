"""Route handler for the fastest lap candidates analysis endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.fastest_lap import FastestLapCandidate
from lapwise.services.analysis.fastest_lap import FastestLapService

router = APIRouter()


@router.get(
    "/fastest-lap-candidates",
    response_model=list[FastestLapCandidate],
    summary="Fastest lap candidates",
    description=(
        "Returns fastest lap probability metrics per driver based on historical "
        "Race and Sprint sessions. Applies SC-period exclusion (110% median threshold) "
        "and credits all tied drivers when multiple drivers share the minimum lap time."
    ),
)
async def fastest_lap_candidates(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    last_n_races: Annotated[int, Query(description="Number of race weekends to include.")] = 12,
    session_key: Annotated[
        int | None,
        Query(
            description=(
                "When provided with include_circuit_history=true, constrains results "
                "to meetings at the same circuit as this session."
            )
        ),
    ] = None,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "When true and session_key is set, merges same-circuit meetings "
                "from the previous 2 calendar years."
            )
        ),
    ] = False,
) -> list[FastestLapCandidate]:
    """Return fastest lap candidate statistics for all drivers in the sample."""
    service = FastestLapService(client)
    return await service.get_fastest_lap_candidates(last_n_races, session_key, include_circuit_history)
