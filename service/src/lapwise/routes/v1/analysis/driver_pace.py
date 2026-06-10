"""GET /v1/analysis/driver-pace-profile — driver pace profile analysis."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.driver_pace import DriverPaceProfile
from lapwise.services.analysis.driver_pace import DriverPaceService

router = APIRouter()


@router.get("/driver-pace-profile", response_model=DriverPaceProfile)
async def driver_pace_profile(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    driver_number: Annotated[int, Query(description="Car number of the driver.")],
    last_n_races: Annotated[
        int, Query(description="Number of race weekends.")
    ] = 12,
    session_key: Annotated[
        int | None,
        Query(description="Constrain to circuit of this session."),
    ] = None,
    include_circuit_history: Annotated[
        bool,
        Query(description="Merge previous 2 years same circuit."),
    ] = False,
) -> DriverPaceProfile:
    """Return a multi-dimensional pace profile for the requested driver."""
    service = DriverPaceService(client)
    return await service.get_driver_pace_profile(
        driver_number, last_n_races, session_key, include_circuit_history
    )
