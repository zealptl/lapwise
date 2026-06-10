"""Analysis router — derived / computed endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth
from lapwise.routes.v1.analysis import fastest_lap

router = APIRouter(
    prefix="/v1/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_auth)],
)

router.include_router(fastest_lap.router)
