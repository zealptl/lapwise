"""Unit tests for analysis common utilities."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.meetings import Meeting
from lapwise.models.sessions import Session
from lapwise.services.analysis.common import (
    get_last_n_meeting_keys,
    get_sessions_for_meetings,
)


def _make_meeting(**overrides: object) -> Meeting:
    defaults: dict[str, object] = {
        "circuit_key": 1,
        "is_cancelled": False,
        "meeting_key": 100,
        "year": 2024,
    }
    defaults.update(overrides)
    return Meeting(**defaults)


def _make_session(**overrides: object) -> Session:
    defaults: dict[str, object] = {
        "circuit_key": 1,
        "is_cancelled": False,
        "meeting_key": 100,
        "session_key": 9000,
        "year": 2024,
    }
    defaults.update(overrides)
    return Session(**defaults)


@pytest.mark.asyncio
async def test_get_last_n_meeting_keys_basic_slice() -> None:
    """Returns only the N most recent meeting keys."""
    client = MagicMock()
    meetings = [
        _make_meeting(meeting_key=1, date_start=datetime(2024, 3, 1)),
        _make_meeting(meeting_key=2, date_start=datetime(2024, 6, 1)),
        _make_meeting(meeting_key=3, date_start=datetime(2024, 9, 1)),
    ]
    client.get = AsyncMock(return_value=meetings)

    result = await get_last_n_meeting_keys(client, n=2)

    assert result == [3, 2]


@pytest.mark.asyncio
async def test_get_last_n_meeting_keys_circuit_key_year_range() -> None:
    """Fetches meetings for each year in range when circuit_key and year_range given."""
    client = MagicMock()

    base_meeting = _make_meeting(meeting_key=10, date_start=datetime(2024, 3, 1), year=2024)
    year_2022_meeting = _make_meeting(meeting_key=20, date_start=datetime(2022, 3, 1), year=2022)
    year_2023_meeting = _make_meeting(meeting_key=30, date_start=datetime(2023, 3, 1), year=2023)

    async def fake_get(path, model, **filters):
        if "circuit_key" in filters:
            y = filters["year"]
            if y == 2022:
                return [year_2022_meeting]
            if y == 2023:
                return [year_2023_meeting]
            return []
        return [base_meeting]

    client.get = AsyncMock(side_effect=fake_get)

    result = await get_last_n_meeting_keys(
        client, n=3, circuit_key=1, year_range=(2022, 2023)
    )

    # Should include all three distinct meetings, most recent first
    assert set(result) == {10, 20, 30}
    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_last_n_meeting_keys_deduplication() -> None:
    """Merges base meetings with range meetings and deduplicates by meeting_key."""
    client = MagicMock()

    shared_meeting = _make_meeting(meeting_key=99, date_start=datetime(2024, 1, 1))

    async def fake_get(path, model, **filters):
        # Both the base query and the year-range query return the same meeting
        return [shared_meeting]

    client.get = AsyncMock(side_effect=fake_get)

    result = await get_last_n_meeting_keys(
        client, n=10, circuit_key=1, year_range=(2024, 2024)
    )

    # meeting_key=99 should appear only once
    assert result.count(99) == 1


@pytest.mark.asyncio
async def test_get_last_n_meeting_keys_sorts_by_date_desc() -> None:
    """Most recent meetings come first in the returned list."""
    client = MagicMock()
    meetings = [
        _make_meeting(meeting_key=1, date_start=datetime(2023, 1, 1)),
        _make_meeting(meeting_key=2, date_start=datetime(2025, 1, 1)),
        _make_meeting(meeting_key=3, date_start=datetime(2024, 1, 1)),
    ]
    client.get = AsyncMock(return_value=meetings)

    result = await get_last_n_meeting_keys(client, n=3)

    assert result == [2, 3, 1]


@pytest.mark.asyncio
async def test_get_sessions_for_meetings_session_type_filter() -> None:
    """Only sessions whose session_type is in session_types are returned."""
    client = MagicMock()
    race_session = _make_session(session_key=1, session_type="Race", meeting_key=100)
    qualifying_session = _make_session(
        session_key=2, session_type="Qualifying", meeting_key=100
    )
    practice_session = _make_session(
        session_key=3, session_type="Practice", meeting_key=100
    )

    client.get = AsyncMock(
        return_value=[race_session, qualifying_session, practice_session]
    )

    result = await get_sessions_for_meetings(
        client, meeting_keys=[100], session_types=["Race", "Qualifying"]
    )

    session_keys = {s.session_key for s in result}
    assert session_keys == {1, 2}
    assert 3 not in session_keys


@pytest.mark.asyncio
async def test_get_sessions_for_meetings_excludes_cancelled() -> None:
    """Sessions with is_cancelled=True are excluded from the results."""
    client = MagicMock()
    active_session = _make_session(session_key=1, session_type="Race", is_cancelled=False)
    cancelled_session = _make_session(
        session_key=2, session_type="Race", is_cancelled=True
    )

    client.get = AsyncMock(return_value=[active_session, cancelled_session])

    result = await get_sessions_for_meetings(
        client, meeting_keys=[100], session_types=["Race"]
    )

    assert len(result) == 1
    assert result[0].session_key == 1


@pytest.mark.asyncio
async def test_get_sessions_for_meetings_parallel_fetch() -> None:
    """asyncio.gather is called once with all per-meeting coroutines."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    with patch(
        "lapwise.services.analysis.common.asyncio.gather", wraps=asyncio.gather
    ) as mock_gather:
        await get_sessions_for_meetings(
            client, meeting_keys=[1, 2, 3], session_types=["Race"]
        )

    mock_gather.assert_called_once()
    # gather should have been called with 3 coroutine arguments (one per meeting)
    assert len(mock_gather.call_args[0]) == 3
