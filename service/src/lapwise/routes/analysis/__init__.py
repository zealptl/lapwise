"""Analysis router — reserved for derived / computed endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth

router = APIRouter(
    prefix="/v1/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_auth)],
)
