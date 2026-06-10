"""Shared utilities for analysis services."""

import asyncio

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
    """Return the most-recent N meeting keys, optionally filtered or merged by circuit history.

    Args:
        client: The OpenF1 HTTP client.
        n: Maximum number of meeting keys to return.
        year: Filter meetings to a specific championship year.
        circuit_key: When provided alongside year_range, fetches meetings for that circuit
            across the given year range and merges them with the standard N-meeting slice.
        year_range: A (start_year, end_year) tuple used with circuit_key for history merging.

    Returns:
        A deduplicated, date-sorted list of meeting keys (most recent first), sliced to N.
    """
    filters: dict[str, object] = {}
    if year is not None:
        filters["year"] = year

    meetings: list[Meeting] = await client.get("meetings", Meeting, **filters)

    # Sort all meetings by date descending
    sorted_meetings = sorted(
        [m for m in meetings if m.date_start is not None],
        key=lambda m: m.date_start,  # type: ignore[arg-type, return-value]
        reverse=True,
    )

    seen: set[int] = set()
    result: list[Meeting] = []

    for m in sorted_meetings:
        if m.meeting_key not in seen:
            seen.add(m.meeting_key)
            result.append(m)
        if len(result) >= n:
            break

    if circuit_key is not None and year_range is not None:
        start_year, end_year = year_range
        circuit_meetings: list[Meeting] = await client.get(
            "meetings", Meeting, circuit_key=circuit_key
        )
        circuit_filtered = [
            m
            for m in circuit_meetings
            if m.year is not None and start_year <= m.year <= end_year
        ]
        for m in circuit_filtered:
            if m.meeting_key not in seen:
                seen.add(m.meeting_key)
                result.append(m)

    return [m.meeting_key for m in result]


async def get_sessions_for_meetings(
    client: OpenF1Client,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Fetch sessions of the given types for a list of meeting keys.

    Requests are made concurrently. Cancelled sessions are excluded.

    Args:
        client: The OpenF1 HTTP client.
        meeting_keys: List of meeting keys to query.
        session_types: List of session type strings to include (e.g. ["Race", "Qualifying"]).

    Returns:
        A flat list of non-cancelled Session instances matching the given types.
    """
    if not meeting_keys:
        return []

    async def fetch_for_meeting(meeting_key: int) -> list[Session]:
        sessions: list[Session] = await client.get("sessions", Session, meeting_key=meeting_key)
        return [
            s
            for s in sessions
            if not s.is_cancelled and s.session_type in session_types
        ]

    results = await asyncio.gather(*[fetch_for_meeting(mk) for mk in meeting_keys])
    return [s for batch in results for s in batch]
