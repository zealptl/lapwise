"""V1 API router - wraps OpenF1 endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth
from lapwise.routes.v1 import (
    championship_drivers,
    championship_teams,
    drivers,
    laps,
    meetings,
    overtakes,
    pit,
    position,
    session_result,
    sessions,
    starting_grid,
    stints,
    weather,
)
from lapwise.routes.v1.analysis import (
    championship_context,
    circuit_profile,
    constructor_pitstop,
    dnf_rates,
    driver_pace,
    fastest_lap,
    overtake_profile,
    qualifying_trends,
)
from lapwise.routes.v1.fantasy import prices as fantasy_prices

router = APIRouter(
    prefix="/v1",
    tags=["OpenF1 wrappers"],
    dependencies=[Depends(get_auth)],
)

router.include_router(sessions.router)
router.include_router(drivers.router)
router.include_router(laps.router)
router.include_router(meetings.router)
router.include_router(overtakes.router)
router.include_router(pit.router)
router.include_router(session_result.router)
router.include_router(stints.router)
router.include_router(position.router)
router.include_router(starting_grid.router)
router.include_router(weather.router)
router.include_router(championship_drivers.router)
router.include_router(championship_teams.router)

# Analysis routes
router.include_router(championship_context.router, prefix="/analysis", tags=["Analysis"])
router.include_router(circuit_profile.router, prefix="/analysis", tags=["Analysis"])
router.include_router(constructor_pitstop.router, prefix="/analysis", tags=["Analysis"])
router.include_router(dnf_rates.router, prefix="/analysis", tags=["Analysis"])
router.include_router(driver_pace.router, prefix="/analysis", tags=["Analysis"])
router.include_router(fastest_lap.router, prefix="/analysis", tags=["Analysis"])
router.include_router(overtake_profile.router, prefix="/analysis", tags=["Analysis"])
router.include_router(qualifying_trends.router, prefix="/analysis", tags=["Analysis"])

# Fantasy routes
router.include_router(fantasy_prices.router, prefix="/fantasy", tags=["Fantasy"])
