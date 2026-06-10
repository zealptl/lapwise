"""Shared utilities for analysis services."""

import asyncio

from lapwise.models.meetings import Meeting
from lapwise.models.sessions import Session

# Laps exceeding this multiple of the session median are treated as safety-car-influenced.
SC_LAP_EXCLUSION_THRESHOLD = 1.10


async def get_last_n_meeting_keys(
    client: object,
    n: int,
    year: int | None = None,
    circuit_key: int | None = None,
    year_range: tuple[int, int] | None = None,
) -> list[int]:
    """Return the meeting_keys for the last *n* meetings matching the given filters.

    Meetings are sorted by date_start descending before slicing to *n*.

    Args:
        client: An :class:`~lapwise.clients.openf1.OpenF1Client` instance.
        n: Maximum number of meeting keys to return.
        year: Optional single year filter.
        circuit_key: Optional circuit filter.
        year_range: Optional ``(start_year, end_year)`` inclusive range; merged and deduplicated
            with any results from the ``year`` filter.

    Returns:
        A deduplicated list of meeting_keys (up to *n*), most recent first.
    """
    from lapwise.clients.openf1 import OpenF1Client  # avoid circular at module level

    c: OpenF1Client = client  # type: ignore[assignment]

    filters: dict[str, object] = {}
    if circuit_key is not None:
        filters["circuit_key"] = circuit_key
    if year is not None:
        filters["year"] = year

    # Fetch the primary set of meetings
    meetings: list[Meeting] = await c.get("meetings", Meeting, **filters)

    # Optionally merge results from a year range
    if year_range is not None:
        start_year, end_year = year_range
        range_filters: dict[str, object] = dict(filters)
        range_filters.pop("year", None)  # year_range supersedes year for range fetch
        tasks = [
            c.get("meetings", Meeting, year=yr, **{k: v for k, v in range_filters.items()})
            for yr in range(start_year, end_year + 1)
        ]
        range_results = await asyncio.gather(*tasks)
        seen_keys: set[int] = {m.meeting_key for m in meetings}
        for batch in range_results:
            for m in batch:
                if m.meeting_key not in seen_keys:
                    meetings.append(m)
                    seen_keys.add(m.meeting_key)

    # Sort by date descending (meetings without a date_start sort last)
    meetings.sort(key=lambda m: m.date_start or 0, reverse=True)  # type: ignore[arg-type]

    # Deduplicate while preserving order
    seen: set[int] = set()
    ordered: list[Meeting] = []
    for m in meetings:
        if m.meeting_key not in seen:
            seen.add(m.meeting_key)
            ordered.append(m)

    return [m.meeting_key for m in ordered[:n]]


async def get_sessions_for_meetings(
    client: object,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Fetch sessions for a list of meeting keys, filtered by session type.

    Cancelled sessions are excluded.  All meeting fetches run in parallel.

    Args:
        client: An :class:`~lapwise.clients.openf1.OpenF1Client` instance.
        meeting_keys: List of meeting_key integers to fetch sessions for.
        session_types: Only sessions whose ``session_type`` is in this list are returned.

    Returns:
        A flat list of non-cancelled :class:`~lapwise.models.sessions.Session` objects.
    """
    from lapwise.clients.openf1 import OpenF1Client  # avoid circular at module level

    c: OpenF1Client = client  # type: ignore[assignment]

    if not meeting_keys:
        return []

    tasks = [c.get("sessions", Session, meeting_key=mk) for mk in meeting_keys]
    results = await asyncio.gather(*tasks)

    sessions: list[Session] = []
    type_set = set(session_types)
    for batch in results:
        for s in batch:
            if s.is_cancelled:
                continue
            if s.session_type in type_set:
                sessions.append(s)

    return sessions
