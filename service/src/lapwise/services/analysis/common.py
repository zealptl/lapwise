"""Shared utilities for analysis services."""

import asyncio
from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.meetings import Meeting
from lapwise.models.sessions import Session

SC_LAP_EXCLUSION_THRESHOLD = 1.10


async def get_last_n_meeting_keys(
    client: OpenF1Client,
    n: int,
    year: int | None = None,
    circuit_key: int | None = None,
    year_range: tuple[int, int] | None = None,
) -> list[int]:
    """Return the last N meeting keys, sorted by date descending.

    Args:
        client: OpenF1 HTTP client.
        n: Maximum number of meeting keys to return.
        year: If provided, restrict to this calendar year.
        circuit_key: If provided, restrict to this circuit.
        year_range: If provided, a (start_year, end_year) tuple used to merge
            additional meetings from a specific date range (inclusive).

    Returns:
        A list of up to N meeting_key integers, sorted most-recent first.
    """
    filters: dict[str, Any] = {}
    if year is not None:
        filters["year"] = year
    if circuit_key is not None:
        filters["circuit_key"] = circuit_key

    meetings: list[Meeting] = await client.get("meetings", Meeting, **filters)

    if year_range is not None:
        start_year, end_year = year_range
        range_filters: dict[str, Any] = {"year_gte": start_year, "year_lte": end_year}
        if circuit_key is not None:
            range_filters["circuit_key"] = circuit_key
        extra: list[Meeting] = await client.get("meetings", Meeting, **range_filters)
        # Merge with deduplication by meeting_key
        existing_keys = {m.meeting_key for m in meetings}
        for m in extra:
            if m.meeting_key not in existing_keys:
                meetings.append(m)
                existing_keys.add(m.meeting_key)

    # Sort by date descending (most recent first), slice to N
    meetings.sort(key=lambda m: m.date_start or "", reverse=True)
    return [m.meeting_key for m in meetings[:n]]


async def get_sessions_for_meetings(
    client: OpenF1Client,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Fetch sessions for the given meeting keys, filtered by session type.

    Fetches in parallel and excludes cancelled sessions.

    Args:
        client: OpenF1 HTTP client.
        meeting_keys: List of meeting_key values to fetch sessions for.
        session_types: List of session_type values to include (e.g. ["Race", "Sprint"]).

    Returns:
        A flat list of non-cancelled Session instances matching the given types.
    """
    if not meeting_keys:
        return []

    async def fetch_for_meeting(meeting_key: int) -> list[Session]:
        return await client.get("sessions", Session, meeting_key=meeting_key)

    results = await asyncio.gather(*[fetch_for_meeting(mk) for mk in meeting_keys])

    sessions: list[Session] = []
    for session_list in results:
        for session in session_list:
            if session.is_cancelled:
                continue
            if session.session_type in session_types:
                sessions.append(session)

    return sessions
