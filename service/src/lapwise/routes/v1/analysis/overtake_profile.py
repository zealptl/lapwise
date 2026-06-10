"""Route handler for GET /v1/analysis/overtake-profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.overtake_profile import OvertakeProfile
from lapwise.services.analysis.overtake_profile import OvertakeProfileService

router = APIRouter()


@router.get("/overtake-profile", response_model=list[OvertakeProfile])
async def overtake_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[int | None, Query(description="Filter to a single driver.")] = None,
    last_n_races: Annotated[
        int, Query(description="Number of race weekends to include.")
    ] = 12,
    session_key: Annotated[
        int | None,
        Query(description="Constrains to the circuit of this session."),
    ] = None,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "Merge meetings from the same circuit across the previous 2 calendar years."
            )
        ),
    ] = False,
) -> list[OvertakeProfile]:
    """Return per-driver overtake statistics from Race and Sprint sessions."""
    service = OvertakeProfileService(client)
    return await service.get_overtake_profiles(
        driver_number, last_n_races, session_key, include_circuit_history
    )
