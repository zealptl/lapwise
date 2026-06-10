"""Shared utilities for analysis services."""

import asyncio
from datetime import datetime

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
    """Return up to N meeting keys sorted by date descending.

    Args:
        client: OpenF1 HTTP client.
        n: Maximum number of meetings to return.
        year: Optional year filter.
        circuit_key: Optional circuit key filter (fetches meetings at that circuit).
        year_range: Optional (start_year, end_year) inclusive range filter.
            When combined with circuit_key, fetches circuit meetings for each year
            in the range and merges/deduplicates with the base set.

    Returns:
        List of meeting_key integers, newest first, capped at n.
    """
    filters: dict[str, object] = {}
    if year is not None:
        filters["year"] = year
    if circuit_key is not None:
        filters["circuit_key"] = circuit_key

    base_meetings: list[Meeting] = await client.get("meetings", Meeting, **filters)

    if year_range is not None and circuit_key is not None:
        start_year, end_year = year_range
        tasks = [
            client.get("meetings", Meeting, circuit_key=circuit_key, year=yr)
            for yr in range(start_year, end_year + 1)
        ]
        results = await asyncio.gather(*tasks)
        extra: list[Meeting] = [m for batch in results for m in batch]
        seen: set[int] = {m.meeting_key for m in base_meetings}
        for m in extra:
            if m.meeting_key not in seen:
                base_meetings.append(m)
                seen.add(m.meeting_key)

    # Sort by date descending (use date_start if available, else meeting_key as tiebreaker)
    def sort_key(m: Meeting) -> tuple[datetime, int]:
        ds = m.date_start if m.date_start is not None else datetime.min
        return (ds, m.meeting_key)

    base_meetings.sort(key=sort_key, reverse=True)
    return [m.meeting_key for m in base_meetings[:n]]


async def get_sessions_for_meetings(
    client: OpenF1Client,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Fetch sessions for a list of meetings, filtered by type, excluding cancelled.

    Args:
        client: OpenF1 HTTP client.
        meeting_keys: List of meeting_key integers to fetch sessions for.
        session_types: Session type strings to include (e.g. ["Race", "Sprint"]).

    Returns:
        Flat list of non-cancelled Session objects matching the requested types.
    """
    if not meeting_keys:
        return []

    tasks = [client.get("sessions", Session, meeting_key=mk) for mk in meeting_keys]
    results = await asyncio.gather(*tasks)

    sessions: list[Session] = []
    session_type_set = set(session_types)
    for batch in results:
        for s in batch:
            if s.is_cancelled:
                continue
            if s.session_type in session_type_set:
                sessions.append(s)
    return sessions
