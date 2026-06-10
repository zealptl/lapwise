"""GET /v1/analysis/circuit-profile — circuit characteristics derived from race data."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.circuit_profile import CircuitProfile
from lapwise.services.analysis.circuit_profile import CircuitProfileService

router = APIRouter()


@router.get(
    "/circuit-profile",
    response_model=CircuitProfile,
    summary="Circuit profile",
    description=(
        "Compute a high-level profile for an F1 circuit from historical race data.\n\n"
        "Derived metrics include overtake difficulty, qualifying importance, safety car tendency, "
        "weather variability, typical tyre compounds, fastest-lap typical lap number, and average "
        "pit stops per driver.\n\n"
        "A minimum of 2 race sessions is required for derived fields; "
        "if fewer are available, derived fields are returned as `null`."
    ),
)
async def circuit_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    last_n_years: Annotated[
        int,
        Query(description="Number of calendar years to include in the analysis window.", ge=1),
    ] = 3,
) -> CircuitProfile:
    """Return a :class:`CircuitProfile` for the requested circuit."""
    service = CircuitProfileService(client)
    return await service.get_circuit_profile(circuit_key, last_n_years)
