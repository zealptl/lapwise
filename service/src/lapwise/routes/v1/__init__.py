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

# Fantasy prices router — no auth dependency; registered separately in main.py
fantasy_router = APIRouter(prefix="/v1/fantasy", tags=["Fantasy"])
fantasy_router.include_router(fantasy_prices.router)
