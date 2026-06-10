"""GET /v1/analysis/constructor-pitstop — constructor pit stop analytics."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.constructor_pitstop import ConstructorPitstop
from lapwise.services.analysis.constructor_pitstop import ConstructorPitstopService

router = APIRouter()


@router.get("/constructor-pitstop", response_model=list[ConstructorPitstop])
async def constructor_pitstop(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    team_name: Annotated[
        str | None,
        Query(description="Filter results to a single constructor by team name."),
    ] = None,
    last_n_races: Annotated[
        int,
        Query(description="Number of recent race weekends to include in the sample.", ge=1),
    ] = 12,
    include_circuit_history: Annotated[
        bool,
        Query(
            description=(
                "Reserved: merge same-circuit meetings from previous calendar years. "
                "Currently falls back to last_n_races behaviour (no circuit context at "
                "this endpoint)."
            )
        ),
    ] = False,
) -> list[ConstructorPitstop]:
    """Return pit stop performance and F1 Fantasy bracket scoring per constructor."""
    service = ConstructorPitstopService(client)
    return await service.get_constructor_pitstops(team_name, last_n_races, include_circuit_history)
