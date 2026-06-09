"""V1 API router - wraps OpenF1 endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth
from lapwise.routes.v1 import drivers, laps, sessions

router = APIRouter(
    prefix="/v1",
    tags=["OpenF1 wrappers"],
    dependencies=[Depends(get_auth)],
)

router.include_router(sessions.router)
router.include_router(drivers.router)
router.include_router(laps.router)
