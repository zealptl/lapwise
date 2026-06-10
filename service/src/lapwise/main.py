"""Lapwise FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lapwise.clients.errors import UpstreamError
from lapwise.clients.openf1 import OpenF1Client
from lapwise.config import get_settings
from lapwise.models.common import ErrorEnvelope
from lapwise.routes.analysis import router as analysis_router
from lapwise.routes.fantasy import router as fantasy_router
from lapwise.routes.v1 import router as v1_router

_OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "OpenF1 wrappers",
        "description": (
            "Thin wrappers around the [OpenF1](https://openf1.org) historical-tier API. "
            "Each endpoint proxies the corresponding OpenF1 resource, applying optional "
            "query-parameter filters before forwarding the request."
        ),
    },
    {
        "name": "Analysis",
        "description": (
            "Derived and computed endpoints that combine multiple OpenF1 resources "
            "to produce higher-level F1 Fantasy insights: driver pace, DNF rates, "
            "fastest-lap candidates, overtake profiles, circuit profiles, championship "
            "context, qualifying trends, and constructor pit stop performance."
        ),
    },
    {
        "name": "Fantasy",
        "description": (
            "F1 Fantasy pricing and recommendation data. Provides the 2025 season "
            "driver and constructor prices used by the LapwiseF1Agent to construct "
            "budget-constrained team recommendations."
        ),
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the lifecycle of shared resources.

    Creates the OpenF1 HTTP client on startup and closes it on shutdown.
    """
    settings = get_settings()
    client = OpenF1Client(settings)
    app.state.openf1_client = client
    try:
        yield
    finally:
        await client.aclose()


def create_app() -> FastAPI:
    """Construct and return the configured FastAPI application."""
    app = FastAPI(
        title="Lapwise — OpenF1 Wrapper API",
        description=(
            "Lapwise wraps the [OpenF1](https://openf1.org) historical-tier API, "
            "providing a typed, filterable REST interface for Formula 1 data including "
            "drivers, laps, pit stops, sessions, stints, weather, and more."
        ),
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=_OPENAPI_TAGS,
        servers=[{"url": "http://localhost:8000", "description": "Local development server"}],
    )

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/healthz", tags=["health"], summary="Health check")
    async def healthz() -> dict[str, str]:
        """Return a static payload confirming the application is running.

        Does **not** contact the OpenF1 upstream.
        """
        return {"status": "ok"}

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(v1_router)
    app.include_router(fantasy_router)
    app.include_router(analysis_router)

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(UpstreamError)
    async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
        if exc.category == "bad_gateway":
            status_code = 502
        elif exc.category == "gateway_timeout":
            status_code = 504
        else:  # forwarded
            status_code = exc.upstream_status or 502

        envelope = ErrorEnvelope(
            detail="OpenF1 upstream error",
            upstream_status=exc.upstream_status,
            upstream_message=exc.upstream_message,
        )
        return JSONResponse(status_code=status_code, content=envelope.model_dump())

    return app


app = create_app()
