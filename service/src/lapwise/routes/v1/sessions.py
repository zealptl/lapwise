"""GET /v1/sessions - OpenF1 sessions wrapper."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_session_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.sessions import Session
from lapwise.services.sessions import SessionService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **sessions** from the OpenF1 API.\n\n"
    "A *session* is a discrete on-track event within a race weekend "
    "(e.g. Practice 1, Qualifying, Sprint, or Race).\n\n"
    "Upstream source: <https://api.openf1.org/v1/sessions>\n\n"
    "All query parameters are optional and combined with AND semantics. "
    "`session_key` accepts an integer or the literal `latest`, "
    "which OpenF1 resolves to the most-recent session."
)

_200_EXAMPLE = [
    {
        "circuit_key": 7,
        "circuit_short_name": "Spa",
        "country_code": "BEL",
        "country_key": 16,
        "country_name": "Belgium",
        "date_end": "2023-07-30T15:35:00+00:00",
        "date_start": "2023-07-30T13:00:00+00:00",
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Spa-Francorchamps",
        "meeting_key": 1216,
        "session_key": 9140,
        "session_name": "Sprint Qualifying",
        "session_type": "Qualifying",
        "year": 2023,
    }
]

_RESPONSES: dict[int | str, dict] = {
    200: {
        "description": "Sessions matching the supplied filters.",
        "content": {"application/json": {"example": _200_EXAMPLE}},
    },
    422: {
        "description": "Validation error - one or more query parameters are invalid.",
        "model": ErrorEnvelope,
    },
    502: {
        "description": "Bad Gateway - OpenF1 returned an unexpected error.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "OpenF1 upstream error",
                    "upstream_status": 503,
                    "upstream_message": "Service Unavailable",
                }
            }
        },
    },
    504: {
        "description": "Gateway Timeout - OpenF1 did not respond in time.",
        "content": {
            "application/json": {
                "example": {
                    "detail": "OpenF1 upstream error",
                    "upstream_status": None,
                    "upstream_message": None,
                }
            }
        },
    },
}


@router.get(
    "/sessions",
    response_model=list[Session],
    summary="List sessions",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_sessions(
    service: Annotated[SessionService, Depends(get_session_service)],
    session_key: Annotated[
        int | Literal["latest"] | None,
        Query(
            description=(
                "Filter by session key. "
                "Use an integer for a specific session or the literal `latest` "
                "to retrieve the most-recent session."
            )
        ),
    ] = None,
    meeting_key: Annotated[
        int | None,
        Query(description="Filter by meeting (race weekend) key."),
    ] = None,
    country_name: Annotated[
        str | None,
        Query(description="Filter by country name (e.g. Belgium)."),
    ] = None,
    session_name: Annotated[
        str | None,
        Query(description="Filter by session name (e.g. Race, Sprint Qualifying)."),
    ] = None,
    session_type: Annotated[
        str | None,
        Query(description="Filter by session type: Race, Qualifying, Practice, or Sprint."),
    ] = None,
    year: Annotated[
        int | None,
        Query(description="Filter by championship year (e.g. 2023)."),
    ] = None,
) -> list[Session]:
    """Return sessions matching the supplied query parameters."""
    return await service.list_sessions(
        session_key=session_key,
        meeting_key=meeting_key,
        country_name=country_name,
        session_name=session_name,
        session_type=session_type,
        year=year,
    )
