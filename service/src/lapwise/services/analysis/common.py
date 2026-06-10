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
    """Fetch meeting keys for the last N race weekends.

    Args:
        client: An OpenF1Client instance.
        n: Maximum number of meeting keys to return.
        year: Optional championship year to filter by.
        circuit_key: Optional circuit key to filter by.
        year_range: Optional (start_year, end_year) inclusive range to query instead of year.
            Results are merged with any year-filtered results and deduplicated.

    Returns:
        A list of meeting_key integers, sorted by date descending, limited to n entries.
    """
    filters: dict[str, object] = {}
    if year is not None:
        filters["year"] = year

    meetings: list[Meeting] = await client.get("meetings", Meeting, **filters)

    if circuit_key is not None:
        meetings = [m for m in meetings if m.circuit_key == circuit_key]

    if year_range is not None:
        start_year, end_year = year_range
        range_meetings: list[Meeting] = []
        for yr in range(start_year, end_year + 1):
            yr_meetings = await client.get("meetings", Meeting, year=yr)
            range_meetings.extend(yr_meetings)
        # Merge and deduplicate by meeting_key
        seen: set[int] = {m.meeting_key for m in meetings}
        for m in range_meetings:
            if m.meeting_key not in seen:
                seen.add(m.meeting_key)
                meetings.append(m)

    # Sort by date_start descending (most recent first), None dates go last
    meetings.sort(key=lambda m: m.date_start or type("", (), {"__lt__": lambda s, o: True})(), reverse=True)  # type: ignore[attr-defined]

    # Simpler sort: filter out None date_start, then sort
    dated = [m for m in meetings if m.date_start is not None]
    undated = [m for m in meetings if m.date_start is None]
    dated.sort(key=lambda m: m.date_start, reverse=True)  # type: ignore[arg-type]
    sorted_meetings = dated + undated

    return [m.meeting_key for m in sorted_meetings[:n]]


async def get_sessions_for_meetings(
    client: OpenF1Client,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Fetch sessions for multiple meetings in parallel, filtered by session_type.

    Args:
        client: An OpenF1Client instance.
        meeting_keys: List of meeting keys to fetch sessions for.
        session_types: List of session type strings to include (e.g. ["Race", "Qualifying"]).

    Returns:
        A flat list of non-cancelled Session instances matching the requested types.
    """
    if not meeting_keys:
        return []

    async def fetch_for_meeting(meeting_key: int) -> list[Session]:
        sessions = await client.get("sessions", Session, meeting_key=meeting_key)
        return [
            s
            for s in sessions
            if not s.is_cancelled and s.session_type in session_types
        ]

    results = await asyncio.gather(*[fetch_for_meeting(mk) for mk in meeting_keys])
    return [session for sessions in results for session in sessions]
