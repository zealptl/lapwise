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
    """Return the meeting_keys for the last N meetings, most recent first.

    Args:
        client: The OpenF1 API client.
        n: Number of most recent meetings to return.
        year: Optional year filter for the base query.
        circuit_key: Optional circuit key for historical range queries.
        year_range: Optional (start, end) year range used together with circuit_key
            to fetch additional historical meetings.

    Returns:
        List of meeting_key integers, sorted by date_start descending, length <= n.
    """
    filters: dict = {}
    if year is not None:
        filters["year"] = year

    meetings: list[Meeting] = await client.get("meetings", Meeting, **filters)

    if circuit_key is not None and year_range is not None:
        start, end = year_range
        extra_meetings_lists = await asyncio.gather(
            *[
                client.get("meetings", Meeting, year=y, circuit_key=circuit_key)
                for y in range(start, end + 1)
            ]
        )
        seen_keys: set[int] = {m.meeting_key for m in meetings}
        for extra_list in extra_meetings_lists:
            for m in extra_list:
                if m.meeting_key not in seen_keys:
                    meetings.append(m)
                    seen_keys.add(m.meeting_key)

    meetings.sort(
        key=lambda m: m.date_start if m.date_start is not None else datetime.min,
        reverse=True,
    )

    return [m.meeting_key for m in meetings[:n]]


async def get_sessions_for_meetings(
    client: OpenF1Client,
    meeting_keys: list[int],
    session_types: list[str],
) -> list[Session]:
    """Return sessions for the given meetings, filtered by session type.

    Fetches sessions for each meeting key in parallel and returns those whose
    session_type is in session_types and that are not cancelled.

    Args:
        client: The OpenF1 API client.
        meeting_keys: List of meeting keys to fetch sessions for.
        session_types: Allowed session type values (e.g. ["Race", "Qualifying"]).

    Returns:
        Flat list of matching, non-cancelled Session instances.
    """
    results: tuple[list[Session], ...] = await asyncio.gather(
        *[client.get("sessions", Session, meeting_key=mk) for mk in meeting_keys]
    )

    sessions: list[Session] = []
    for session_list in results:
        for s in session_list:
            if s.session_type in session_types and not s.is_cancelled:
                sessions.append(s)

    return sessions
