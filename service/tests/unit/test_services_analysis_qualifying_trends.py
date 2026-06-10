"""Unit tests for QualifyingTrendsService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.analysis.qualifying_trends import QualifyingTrends
from lapwise.models.championship import ChampionshipDriver
from lapwise.models.laps import Lap
from lapwise.models.sessions import Session
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.services.analysis.qualifying_trends import QualifyingTrendsService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRIVER = 16


def _session(session_key: int, meeting_key: int, date_offset: int = 0) -> Session:
    from datetime import datetime, timezone

    return Session(
        circuit_key=1,
        is_cancelled=False,
        meeting_key=meeting_key,
        session_key=session_key,
        session_type="Qualifying",
        year=2024,
        date_start=datetime(2024, 1, date_offset + 1, tzinfo=timezone.utc),
    )


def _grid_entry(
    driver_number: int, position: int, session_key: int, meeting_key: int
) -> StartingGridEntry:
    return StartingGridEntry(
        driver_number=driver_number,
        position=position,
        session_key=session_key,
        meeting_key=meeting_key,
    )


def _lap(
    driver_number: int,
    session_key: int,
    meeting_key: int,
    s1: float | None = 25.0,
    s2: float | None = 30.0,
    s3: float | None = 22.0,
) -> Lap:
    return Lap(
        driver_number=driver_number,
        lap_number=1,
        session_key=session_key,
        meeting_key=meeting_key,
        duration_sector_1=s1,
        duration_sector_2=s2,
        duration_sector_3=s3,
    )


def _champ(driver_number: int, position_current: int, meeting_key: int) -> ChampionshipDriver:
    return ChampionshipDriver(
        driver_number=driver_number,
        meeting_key=meeting_key,
        points_current=100.0,
        points_start=75.0,
        position_current=position_current,
        position_start=position_current,
        session_key=9000,
    )


def _make_client(
    meeting_keys: list[int],
    sessions: list[Session],
    grid_by_session: dict[int, list[StartingGridEntry]],
    laps_by_session: dict[int, list[Lap]],
    champ_by_meeting: dict[int, list[ChampionshipDriver]],
) -> MagicMock:
    """Build a mock OpenF1Client that returns canned data."""
    from lapwise.models.meetings import Meeting
    from datetime import datetime, timezone

    meetings_list = [
        Meeting(
            circuit_key=1,
            is_cancelled=False,
            meeting_key=mk,
            year=2024,
            date_start=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
        )
        for i, mk in enumerate(reversed(meeting_keys))  # ascending; client returns all
    ]

    async def _get(path: str, model, **filters):
        if path == "meetings":
            return meetings_list
        if path == "sessions":
            mk = filters.get("meeting_key")
            return [s for s in sessions if s.meeting_key == mk]
        if path == "starting_grid":
            sk = filters.get("session_key")
            return grid_by_session.get(sk, [])
        if path == "laps":
            sk = filters.get("session_key")
            return laps_by_session.get(sk, [])
        if path == "championship_drivers":
            mk = filters.get("meeting_key")
            return champ_by_meeting.get(mk, [])
        return []

    client = MagicMock()
    client.get = AsyncMock(side_effect=_get)
    return client


# ---------------------------------------------------------------------------
# Test 1: Q3 appearance rate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qualifying_trends_q3_appearance_rate() -> None:
    """Driver in top 10 in 8 of 12 sessions → q3_appearance_rate ≈ 0.667."""
    n = 12
    meeting_keys = list(range(1001, 1001 + n))
    sessions = [_session(session_key=2000 + i, meeting_key=mk, date_offset=i) for i, mk in enumerate(meeting_keys)]

    grid_by_session: dict[int, list[StartingGridEntry]] = {}
    for i, s in enumerate(sessions):
        # First 8 sessions: top-10 positions (1–10); last 4: positions 11–14
        pos = (i % 10) + 1 if i < 8 else 11 + (i - 8)
        grid_by_session[s.session_key] = [
            _grid_entry(DRIVER, pos, s.session_key, s.meeting_key)
        ]

    laps_by_session = {s.session_key: [] for s in sessions}
    champ_by_meeting = {s.meeting_key: [] for s in sessions}

    client = _make_client(meeting_keys, sessions, grid_by_session, laps_by_session, champ_by_meeting)
    service = QualifyingTrendsService(client)
    result: QualifyingTrends = await service.get_qualifying_trends(DRIVER, last_n_races=n)

    assert result.q3_appearance_rate is not None
    assert abs(result.q3_appearance_rate - 8 / 12) < 0.01


# ---------------------------------------------------------------------------
# Test 2: Sector dominance leader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qualifying_trends_sector_dominance_leader() -> None:
    """Driver sets fastest S1 in 7 of 12 sessions → sector 1 dominance_rate ≈ 0.583."""
    n = 12
    meeting_keys = list(range(2001, 2001 + n))
    sessions = [_session(session_key=3000 + i, meeting_key=mk, date_offset=i) for i, mk in enumerate(meeting_keys)]

    grid_by_session = {
        s.session_key: [_grid_entry(DRIVER, 5, s.session_key, s.meeting_key)] for s in sessions
    }

    other_driver = 1
    laps_by_session: dict[int, list[Lap]] = {}
    for i, s in enumerate(sessions):
        if i < 7:
            # Our driver sets the fastest S1
            driver_lap = _lap(DRIVER, s.session_key, s.meeting_key, s1=24.0)
            other_lap = _lap(other_driver, s.session_key, s.meeting_key, s1=25.0)
        else:
            # Other driver sets fastest S1
            driver_lap = _lap(DRIVER, s.session_key, s.meeting_key, s1=25.5)
            other_lap = _lap(other_driver, s.session_key, s.meeting_key, s1=24.0)
        laps_by_session[s.session_key] = [driver_lap, other_lap]

    champ_by_meeting = {s.meeting_key: [] for s in sessions}

    client = _make_client(meeting_keys, sessions, grid_by_session, laps_by_session, champ_by_meeting)
    service = QualifyingTrendsService(client)
    result: QualifyingTrends = await service.get_qualifying_trends(DRIVER, last_n_races=n)

    dom = result.sector_dominance.sector_1
    assert dom.dominance_rate is not None
    assert abs(dom.dominance_rate - 7 / 12) < 0.01


# ---------------------------------------------------------------------------
# Test 3: Overperforming in quali (grid_vs_expected negative)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qualifying_trends_overperforming_in_quali() -> None:
    """Driver qualifies P3 while championship position is P7 → grid_vs_expected < 0."""
    meeting_keys = [5001]
    sessions = [_session(session_key=6001, meeting_key=5001, date_offset=1)]

    grid_by_session = {6001: [_grid_entry(DRIVER, 3, 6001, 5001)]}
    laps_by_session = {6001: []}
    champ_by_meeting = {5001: [_champ(DRIVER, 7, 5001)]}

    client = _make_client(meeting_keys, sessions, grid_by_session, laps_by_session, champ_by_meeting)
    service = QualifyingTrendsService(client)
    result: QualifyingTrends = await service.get_qualifying_trends(DRIVER, last_n_races=1)

    assert result.grid_vs_expected is not None
    assert result.grid_vs_expected < 0  # grid P3 − champ P7 = -4


# ---------------------------------------------------------------------------
# Test 4: Missing sector data excluded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qualifying_trends_missing_sector_data() -> None:
    """Sessions with >50% null sector data are excluded from sector averages."""
    meeting_keys = [7001, 7002]
    sessions = [
        _session(session_key=8001, meeting_key=7001, date_offset=1),
        _session(session_key=8002, meeting_key=7002, date_offset=2),
    ]

    grid_by_session = {
        8001: [_grid_entry(DRIVER, 5, 8001, 7001)],
        8002: [_grid_entry(DRIVER, 5, 8002, 7002)],
    }

    # Session 8001: all laps have null S1 → should be excluded
    null_laps = [
        Lap(
            driver_number=DRIVER,
            lap_number=1,
            session_key=8001,
            meeting_key=7001,
            duration_sector_1=None,
            duration_sector_2=None,
            duration_sector_3=None,
        )
        for _ in range(5)
    ]
    # Session 8002: valid sector data
    valid_laps = [_lap(DRIVER, 8002, 7002, s1=25.0, s2=30.0, s3=22.0)]

    laps_by_session = {8001: null_laps, 8002: valid_laps}
    champ_by_meeting = {7001: [], 7002: []}

    client = _make_client(meeting_keys, sessions, grid_by_session, laps_by_session, champ_by_meeting)
    service = QualifyingTrendsService(client)
    result: QualifyingTrends = await service.get_qualifying_trends(DRIVER, last_n_races=2)

    # Only session 8002 contributes to sector stats
    # delta should be 0 (driver IS the only driver, so driver_best == field_min)
    assert result.sector_dominance.sector_1.avg_delta_to_fastest is not None
    # The dominance rate for sector 1 should be 1.0 (sole entry equals field min)
    assert result.sector_dominance.sector_1.dominance_rate == 1.0


# ---------------------------------------------------------------------------
# Test 5: Recent trend IMPROVING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qualifying_trends_recent_trend_improving() -> None:
    """Newer sessions avg position < older * 0.90 → recent_trend == IMPROVING."""
    # 4 sessions: older two at P15, newer two at P5
    meeting_keys = [9001, 9002, 9003, 9004]
    sessions = [
        _session(session_key=10001 + i, meeting_key=9001 + i, date_offset=i + 1)
        for i in range(4)
    ]

    grid_by_session = {}
    for i, s in enumerate(sessions):
        pos = 15 if i < 2 else 5  # older = P15, newer = P5
        grid_by_session[s.session_key] = [_grid_entry(DRIVER, pos, s.session_key, s.meeting_key)]

    laps_by_session = {s.session_key: [] for s in sessions}
    champ_by_meeting = {s.meeting_key: [] for s in sessions}

    client = _make_client(meeting_keys, sessions, grid_by_session, laps_by_session, champ_by_meeting)
    service = QualifyingTrendsService(client)
    result: QualifyingTrends = await service.get_qualifying_trends(DRIVER, last_n_races=4)

    assert result.recent_trend == "IMPROVING"
