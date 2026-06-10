"""GET /v1/analysis/championship-context — Championship context endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_openf1_client
from lapwise.models.analysis.championship_context import ChampionshipContext
from lapwise.services.analysis.championship_context import ChampionshipContextService

router = APIRouter()


@router.get(
    "/championship-context",
    response_model=ChampionshipContext,
    summary="Championship context snapshot",
    description=(
        "Returns a computed championship context for a given season, including per-driver "
        "momentum (POSITIVE/NEUTRAL/NEGATIVE), desperation index (0–100), and constructor "
        "battle flags.  Optionally filter to standings as of a specific meeting via "
        "`after_round`."
    ),
)
async def championship_context(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
    season: Annotated[
        int | None,
        Query(description="Championship year.  Defaults to the current calendar year."),
    ] = None,
    after_round: Annotated[
        int | None,
        Query(
            description=(
                "Return standings after this meeting_key.  Only meetings with "
                "meeting_key <= after_round are included in the calculation."
            )
        ),
    ] = None,
) -> ChampionshipContext:
    """Return a full championship context snapshot for drivers and constructors."""
    service = ChampionshipContextService(client)
    return await service.get_championship_context(season, after_round)
