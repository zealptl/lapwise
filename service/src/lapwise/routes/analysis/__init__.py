"""Analysis router — derived / computed endpoints combining multiple OpenF1 resources."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from lapwise.clients.openf1 import OpenF1Client
from lapwise.deps import get_analysis_service, get_auth, get_openf1_client
from lapwise.models.analysis import (
    ChampionshipContext,
    CircuitProfile,
    ConstructorPitstop,
    DnfRates,
    DriverPaceProfile,
    FastestLapCandidate,
    QualifyingTrend,
)
from lapwise.routes.v1.analysis import overtake_profile as overtake_profile_router
from lapwise.services.analysis import AnalysisService
from lapwise.services.analysis.constructor_pitstop import ConstructorPitstopService

router = APIRouter(
    prefix="/v1/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_auth)],
)

# Spec-compliant overtake profile endpoint (tasks 6.1–6.3)
router.include_router(overtake_profile_router.router)


@router.get(
    "/driver-pace-profile",
    response_model=DriverPaceProfile,
    summary="Driver pace profile",
    description=(
        "Aggregate race lap times and stint lengths for a driver at a specific circuit and year. "
        "When `include_circuit_history=true`, also fetches data for the previous two years to "
        "enable historical trend analysis."
    ),
)
async def get_driver_pace_profile(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    driver_number: Annotated[int, Query(description="Car number of the driver.")],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    year: Annotated[int, Query(description="Championship year.")],
    include_circuit_history: Annotated[
        bool,
        Query(description="When true, include data for year-1 and year-2 at this circuit."),
    ] = False,
) -> DriverPaceProfile:
    return await svc.get_driver_pace_profile(
        driver_number=driver_number,
        circuit_key=circuit_key,
        year=year,
        include_circuit_history=include_circuit_history,
    )


@router.get(
    "/dnf-rates",
    response_model=DnfRates,
    summary="DNF rates",
    description=(
        "Compute per-driver and per-constructor DNF (Did Not Finish) rates at a circuit "
        "over a configurable sample window of recent races. A DNF is recorded when a "
        "driver's classified position is absent or 20+."
    ),
)
async def get_dnf_rates(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    year: Annotated[int, Query(description="Reference championship year.")],
    last_n_races: Annotated[
        int,
        Query(description="Maximum number of most-recent races to include in the sample.", ge=1),
    ] = 5,
    include_circuit_history: Annotated[
        bool,
        Query(description="When true, expand the sample to include races from year-1 and year-2."),
    ] = False,
) -> DnfRates:
    return await svc.get_dnf_rates(
        circuit_key=circuit_key,
        year=year,
        last_n_races=last_n_races,
        include_circuit_history=include_circuit_history,
    )


@router.get(
    "/fastest-lap-candidates",
    response_model=list[FastestLapCandidate],
    summary="Fastest lap candidates",
    description=(
        "Rank drivers by how often they have recorded the fastest lap at a circuit "
        "across up to five historical seasons. Results are ordered by fastest-lap count "
        "descending."
    ),
)
async def get_fastest_lap_candidates(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    year: Annotated[int, Query(description="Most-recent championship year to include.")],
) -> list[FastestLapCandidate]:
    return await svc.get_fastest_lap_candidates(circuit_key=circuit_key, year=year)


@router.get(
    "/circuit-profile",
    response_model=CircuitProfile,
    summary="Circuit profile",
    description=(
        "Compute high-level circuit characteristics from historical session data: "
        "overtaking difficulty (low/medium/high), average pit stop frequency, "
        "observed tyre strategies (compounds), and a safety car probability estimate "
        "derived from rainfall-affected laps."
    ),
)
async def get_circuit_profile(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    year: Annotated[int, Query(description="Championship year.")],
) -> CircuitProfile:
    return await svc.get_circuit_profile(circuit_key=circuit_key, year=year)


@router.get(
    "/championship-context",
    response_model=ChampionshipContext,
    summary="Championship context",
    description=(
        "Return the current driver and constructor championship standings for a given year. "
        "Data is sourced from the most-recent championship update per driver/team."
    ),
)
async def get_championship_context(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    year: Annotated[int, Query(description="Championship year.")],
    last_n_races: Annotated[
        int,
        Query(description="Included for API consistency; not yet used in standings computation."),
    ] = 5,
) -> ChampionshipContext:
    return await svc.get_championship_context(year=year, last_n_races=last_n_races)


@router.get(
    "/qualifying-trends",
    response_model=list[QualifyingTrend],
    summary="Qualifying trends",
    description=(
        "Return per-driver average qualifying position and Q3 appearance frequency "
        "at a circuit across up to five historical seasons. Results are sorted by "
        "average qualifying position ascending (better qualifiers first)."
    ),
)
async def get_qualifying_trends(
    svc: Annotated[AnalysisService, Depends(get_analysis_service)],
    circuit_key: Annotated[int, Query(description="OpenF1 circuit identifier.")],
    year: Annotated[int, Query(description="Most-recent championship year to include.")],
) -> list[QualifyingTrend]:
    return await svc.get_qualifying_trends(circuit_key=circuit_key, year=year)


@router.get(
    "/constructor-pitstop",
    response_model=list[ConstructorPitstop],
    summary="Constructor pit stop performance",
    description=(
        "Return per-constructor pit stop statistics including F1 Fantasy bracket scoring, "
        "fastest pitstop rate, sub-2s rate, and consistency score across recent race weekends."
    ),
)
async def get_constructor_pitstop(
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
        Query(description="Reserved: currently falls back to last_n_races behaviour."),
    ] = False,
) -> list[ConstructorPitstop]:
    service = ConstructorPitstopService(client)
    return await service.get_constructor_pitstops(team_name, last_n_races, include_circuit_history)
