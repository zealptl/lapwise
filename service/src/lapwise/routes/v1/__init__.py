"""V1 API router - wraps OpenF1 endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth
from lapwise.routes.v1 import (
    drivers,
    laps,
    meetings,
    overtakes,
    pit,
    position,
    session_result,
    sessions,
    stints,
)

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
