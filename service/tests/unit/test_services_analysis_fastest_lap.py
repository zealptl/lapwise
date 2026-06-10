"""Unit tests for FastestLapService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.analysis.fastest_lap import FastestLapCandidate
from lapwise.models.laps import Lap
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.models.stints import Stint
from lapwise.services.analysis.fastest_lap import FastestLapService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(
    session_key: int = 1,
    meeting_key: int = 100,
    session_type: str = "Race",
    is_cancelled: bool = False,
    circuit_key: int = 10,
) -> Session:
    return Session(
        session_key=session_key,
        meeting_key=meeting_key,
        session_type=session_type,
        is_cancelled=is_cancelled,
        circuit_key=circuit_key,
        circuit_short_name="Test",
        country_code="TST",
        country_key=1,
        country_name="Testland",
        date_end=None,
        date_start=None,
        gmt_offset="00:00:00",
        location="Testville",
        session_name=session_type,
        year=2025,
    )


def _make_lap(
    driver_number: int = 1,
    lap_number: int = 10,
    lap_duration: float | None = 90.0,
    is_pit_out_lap: bool | None = False,
    session_key: int = 1,
    meeting_key: int = 100,
) -> Lap:
    return Lap(
        driver_number=driver_number,
        lap_number=lap_number,
        lap_duration=lap_duration,
        is_pit_out_lap=is_pit_out_lap,
        session_key=session_key,
        meeting_key=meeting_key,
        date_start=None,
        duration_sector_1=None,
        duration_sector_2=None,
        duration_sector_3=None,
        i1_speed=None,
        i2_speed=None,
        segments_sector_1=None,
        segments_sector_2=None,
        segments_sector_3=None,
        st_speed=None,
    )


def _make_stint(
    driver_number: int = 1,
    lap_start: int = 1,
    lap_end: int | None = 50,
    tyre_age_at_start: int | None = 0,
    session_key: int = 1,
    meeting_key: int = 100,
) -> Stint:
    return Stint(
        driver_number=driver_number,
        lap_start=lap_start,
        lap_end=lap_end,
        tyre_age_at_start=tyre_age_at_start,
        session_key=session_key,
        meeting_key=meeting_key,
        compound="SOFT",
        stint_number=1,
    )


def _make_session_result(
    driver_number: int = 1,
    position: int | None = 1,
    session_key: int = 1,
    meeting_key: int = 100,
) -> SessionResult:
    return SessionResult(
        driver_number=driver_number,
        position=position,
        session_key=session_key,
        meeting_key=meeting_key,
        dnf=False,
        dns=False,
        dsq=False,
        duration=None,
        gap_to_leader=None,
        number_of_laps=None,
    )


# ---------------------------------------------------------------------------
# Test 1: Standard fastest lap candidates request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fastest_lap_candidates_standard() -> None:
    """Returns a list with fl_rate computed for each driver seen."""
    client = MagicMock()
    session = _make_session(session_key=1, meeting_key=100)

    # Driver 1: lap_duration 89.0 (fastest), Driver 2: lap_duration 91.0
    lap1 = _make_lap(driver_number=1, lap_number=5, lap_duration=89.0)
    lap2 = _make_lap(driver_number=2, lap_number=5, lap_duration=91.0)

    stint1 = _make_stint(driver_number=1, lap_start=1, lap_end=50, tyre_age_at_start=0)
    stint2 = _make_stint(driver_number=2, lap_start=1, lap_end=50, tyre_age_at_start=0)

    result1 = _make_session_result(driver_number=1, position=3)
    result2 = _make_session_result(driver_number=2, position=1)

    with (
        patch(
            "lapwise.services.analysis.fastest_lap.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[100]),
        ),
        patch(
            "lapwise.services.analysis.fastest_lap.get_sessions_for_meetings",
            new=AsyncMock(return_value=[session]),
        ),
    ):
        client.get = AsyncMock(side_effect=[
            [lap1, lap2],     # laps for session 1
            [stint1, stint2], # stints for session 1
            [result1, result2],  # session_result for session 1
        ])

        service = FastestLapService(client)
        candidates = await service.get_fastest_lap_candidates(last_n_races=12)

    assert isinstance(candidates, list)
    assert len(candidates) == 2

    by_driver = {c.driver_number: c for c in candidates}

    # Driver 1 set the FL
    assert by_driver[1].fastest_lap_count == 1
    assert by_driver[1].fl_rate == pytest.approx(1.0)
    assert by_driver[1].total_sessions == 1
    assert by_driver[1].sample_races == 1

    # Driver 2 did not set FL
    assert by_driver[2].fastest_lap_count == 0
    assert by_driver[2].fl_rate == pytest.approx(0.0)
    assert by_driver[2].fl_on_fresh_tyre_rate is None


# ---------------------------------------------------------------------------
# Test 2: SC exclusion — laps above 110% median are excluded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fastest_lap_sc_exclusion() -> None:
    """Laps above 110% of session median are excluded from FL consideration."""
    client = MagicMock()
    session = _make_session(session_key=2, meeting_key=200)

    # median of [90, 90, 90] = 90; threshold = 99.0
    # "normal" laps at 90s, but SC lap at 150s; the 150s lap should NOT win
    lap_normal1 = _make_lap(driver_number=1, lap_number=3, lap_duration=90.0, session_key=2, meeting_key=200)
    lap_normal2 = _make_lap(driver_number=2, lap_number=3, lap_duration=90.0, session_key=2, meeting_key=200)
    # This lap is behind SC so it's very slow — above threshold
    lap_sc = _make_lap(driver_number=3, lap_number=3, lap_duration=150.0, session_key=2, meeting_key=200)

    stint1 = _make_stint(driver_number=1, session_key=2, meeting_key=200)
    stint2 = _make_stint(driver_number=2, session_key=2, meeting_key=200)
    stint3 = _make_stint(driver_number=3, session_key=2, meeting_key=200)

    result1 = _make_session_result(driver_number=1, position=1, session_key=2, meeting_key=200)
    result2 = _make_session_result(driver_number=2, position=2, session_key=2, meeting_key=200)
    result3 = _make_session_result(driver_number=3, position=3, session_key=2, meeting_key=200)

    with (
        patch(
            "lapwise.services.analysis.fastest_lap.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[200]),
        ),
        patch(
            "lapwise.services.analysis.fastest_lap.get_sessions_for_meetings",
            new=AsyncMock(return_value=[session]),
        ),
    ):
        client.get = AsyncMock(side_effect=[
            [lap_normal1, lap_normal2, lap_sc],
            [stint1, stint2, stint3],
            [result1, result2, result3],
        ])

        service = FastestLapService(client)
        candidates = await service.get_fastest_lap_candidates()

    by_driver = {c.driver_number: c for c in candidates}

    # Driver 3 with the 150s SC lap must NOT win
    assert by_driver[3].fastest_lap_count == 0

    # Drivers 1 and 2 share the minimum at 90s — both get credit (tied FL, see test 3)
    # but crucially driver 3 does not
    assert by_driver[3].fl_rate == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Test 3: Tied fastest lap — both drivers receive credit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fastest_lap_tied_fl() -> None:
    """Two drivers with equal minimum lap_duration both receive FL credit."""
    client = MagicMock()
    session = _make_session(session_key=3, meeting_key=300)

    # Both drivers post 88.5s — a tie
    lap1 = _make_lap(driver_number=10, lap_number=20, lap_duration=88.5, session_key=3, meeting_key=300)
    lap2 = _make_lap(driver_number=11, lap_number=20, lap_duration=88.5, session_key=3, meeting_key=300)
    lap3 = _make_lap(driver_number=12, lap_number=20, lap_duration=90.0, session_key=3, meeting_key=300)

    stints = [
        _make_stint(driver_number=10, session_key=3, meeting_key=300),
        _make_stint(driver_number=11, session_key=3, meeting_key=300),
        _make_stint(driver_number=12, session_key=3, meeting_key=300),
    ]
    results = [
        _make_session_result(driver_number=10, position=1, session_key=3, meeting_key=300),
        _make_session_result(driver_number=11, position=2, session_key=3, meeting_key=300),
        _make_session_result(driver_number=12, position=3, session_key=3, meeting_key=300),
    ]

    with (
        patch(
            "lapwise.services.analysis.fastest_lap.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[300]),
        ),
        patch(
            "lapwise.services.analysis.fastest_lap.get_sessions_for_meetings",
            new=AsyncMock(return_value=[session]),
        ),
    ):
        client.get = AsyncMock(side_effect=[
            [lap1, lap2, lap3],
            stints,
            results,
        ])

        service = FastestLapService(client)
        candidates = await service.get_fastest_lap_candidates()

    by_driver = {c.driver_number: c for c in candidates}

    # Both tied drivers must have FL credit
    assert by_driver[10].fastest_lap_count == 1
    assert by_driver[11].fastest_lap_count == 1

    # Non-tied driver must not
    assert by_driver[12].fastest_lap_count == 0


# ---------------------------------------------------------------------------
# Test 4: Fresh tyre detection — fl_on_fresh_tyre_rate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fastest_lap_fresh_tyre_detection() -> None:
    """fl_on_fresh_tyre_rate is incremented when tyre_age <= 2 at the FL lap."""
    client = MagicMock()
    session = _make_session(session_key=4, meeting_key=400)

    # Driver 5 sets the FL on lap 2; stint started lap 1 with tyre_age_at_start=0
    # => tyre_age = 2 - 1 + 0 = 1  (fresh tyre)
    fl_lap = _make_lap(driver_number=5, lap_number=2, lap_duration=85.0, session_key=4, meeting_key=400)
    other_lap = _make_lap(driver_number=6, lap_number=2, lap_duration=87.0, session_key=4, meeting_key=400)

    # Stint for driver 5: started lap 1, tyre_age_at_start=0 → tyre_age at lap 2 = 1
    stint_fresh = _make_stint(
        driver_number=5, lap_start=1, lap_end=20, tyre_age_at_start=0,
        session_key=4, meeting_key=400,
    )
    stint_other = _make_stint(
        driver_number=6, lap_start=1, lap_end=20, tyre_age_at_start=0,
        session_key=4, meeting_key=400,
    )

    results = [
        _make_session_result(driver_number=5, position=1, session_key=4, meeting_key=400),
        _make_session_result(driver_number=6, position=2, session_key=4, meeting_key=400),
    ]

    with (
        patch(
            "lapwise.services.analysis.fastest_lap.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[400]),
        ),
        patch(
            "lapwise.services.analysis.fastest_lap.get_sessions_for_meetings",
            new=AsyncMock(return_value=[session]),
        ),
    ):
        client.get = AsyncMock(side_effect=[
            [fl_lap, other_lap],
            [stint_fresh, stint_other],
            results,
        ])

        service = FastestLapService(client)
        candidates = await service.get_fastest_lap_candidates()

    by_driver = {c.driver_number: c for c in candidates}

    assert by_driver[5].fastest_lap_count == 1
    assert by_driver[5].fl_on_fresh_tyre_rate == pytest.approx(1.0)  # tyre_age=1 <= 2

    # Driver 6 has no FL
    assert by_driver[6].fl_on_fresh_tyre_rate is None


# ---------------------------------------------------------------------------
# Test 5: Circuit history — include_circuit_history=True triggers circuit filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fastest_lap_circuit_history() -> None:
    """When include_circuit_history=True and session_key set, client is called for circuit filter."""
    client = MagicMock()
    session = _make_session(session_key=9165, meeting_key=500, circuit_key=42)

    fl_lap = _make_lap(driver_number=1, lap_number=10, lap_duration=80.0, session_key=9165, meeting_key=500)
    stint = _make_stint(driver_number=1, session_key=9165, meeting_key=500)
    result = _make_session_result(driver_number=1, position=1, session_key=9165, meeting_key=500)

    # client.get: first call fetches sessions to get circuit_key, then laps/stints/results
    with (
        patch(
            "lapwise.services.analysis.fastest_lap.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[500]),
        ) as mock_get_meetings,
        patch(
            "lapwise.services.analysis.fastest_lap.get_sessions_for_meetings",
            new=AsyncMock(return_value=[session]),
        ),
    ):
        client.get = AsyncMock(side_effect=[
            [session],    # sessions lookup to get circuit_key
            [fl_lap],     # laps
            [stint],      # stints
            [result],     # session_result
        ])

        service = FastestLapService(client)
        candidates = await service.get_fastest_lap_candidates(
            last_n_races=5,
            session_key=9165,
            include_circuit_history=True,
        )

    # Verify get_last_n_meeting_keys was called with circuit_key and year_range
    mock_get_meetings.assert_called_once()
    call_kwargs = mock_get_meetings.call_args
    assert call_kwargs.kwargs.get("circuit_key") == 42
    year_range = call_kwargs.kwargs.get("year_range")
    assert year_range is not None
    assert len(year_range) == 2
    # year_range should be (current_year - 2, current_year - 1)
    start_yr, end_yr = year_range
    assert end_yr == start_yr + 1

    # Results should still contain driver 1
    by_driver = {c.driver_number: c for c in candidates}
    assert 1 in by_driver
    assert by_driver[1].fastest_lap_count == 1
