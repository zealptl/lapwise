"""V1 API router — wraps OpenF1 endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth

router = APIRouter(
    prefix="/v1",
    tags=["OpenF1 wrappers"],
    dependencies=[Depends(get_auth)],
)
