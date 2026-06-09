"""GET /v1/meetings - OpenF1 meetings wrapper."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from lapwise.deps import get_meeting_service
from lapwise.models.common import ErrorEnvelope
from lapwise.models.meetings import Meeting
from lapwise.services.meetings import MeetingService

router = APIRouter()

_DESCRIPTION = (
    "Retrieve Formula 1 **race weekend meetings** from the OpenF1 API.\n\n"
    "A *meeting* is an entire race weekend, encompassing all practice sessions, "
    "qualifying, sprint, and race sessions at a single circuit.\n\n"
    "Upstream source: <https://api.openf1.org/v1/meetings>\n\n"
    "All query parameters are optional and combined with AND semantics. "
    "`meeting_key` accepts an integer or the literal `latest`, "
    "which OpenF1 resolves to the most-recent race weekend."
)

_200_EXAMPLE = [
    {
        "circuit_key": 16,
        "circuit_info_url": None,
        "circuit_image": None,
        "circuit_short_name": "Monza",
        "circuit_type": "permanent",
        "country_code": "ITA",
        "country_flag": None,
        "country_key": 13,
        "country_name": "Italy",
        "date_end": "2023-09-03T15:00:00+00:00",
        "date_start": "2023-08-31T11:30:00+00:00",
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Monza",
        "meeting_key": 1219,
        "meeting_name": "Italian Grand Prix",
        "meeting_official_name": "Formula 1 Pirelli Gran Premio d'Italia 2023",
        "year": 2023,
    }
]

_RESPONSES: dict[int | str, dict[str, object]] = {
    200: {
        "description": "Meetings matching the supplied filters.",
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
    "/meetings",
    response_model=list[Meeting],
    summary="List meetings",
    description=_DESCRIPTION,
    responses=_RESPONSES,
)
async def list_meetings(
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    meeting_key: Annotated[
        int | Literal["latest"] | None,
        Query(
            description=(
                "Filter by meeting key. "
                "Use an integer for a specific meeting or the literal `latest` "
                "to retrieve the most-recent race weekend."
            )
        ),
    ] = None,
    year: Annotated[
        int | None,
        Query(description="Filter by championship year (e.g. 2023)."),
    ] = None,
    country_name: Annotated[
        str | None,
        Query(description="Filter by country name (e.g. Italy)."),
    ] = None,
    circuit_short_name: Annotated[
        str | None,
        Query(description="Filter by circuit short name (e.g. Monza)."),
    ] = None,
    location: Annotated[
        str | None,
        Query(description="Filter by city or venue name."),
    ] = None,
) -> list[Meeting]:
    """Return meetings matching the supplied query parameters."""
    return await service.list_meetings(
        meeting_key=meeting_key,
        year=year,
        country_name=country_name,
        circuit_short_name=circuit_short_name,
        location=location,
    )
