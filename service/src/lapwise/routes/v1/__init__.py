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
from lapwise.routes.v1.analysis import qualifying_trends as analysis_qualifying_trends

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
router.include_router(
    analysis_qualifying_trends.router,
    prefix="/analysis",
    tags=["Analysis"],
)
