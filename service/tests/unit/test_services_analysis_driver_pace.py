"""Unit tests for DriverPaceService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.analysis.driver_pace import DriverPaceProfile
from lapwise.models.laps import Lap
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.models.stints import Stint
from lapwise.services.analysis.driver_pace import DriverPaceService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(session_key: int = 1, meeting_key: int = 100, circuit_key: int = 6) -> Session:
    return Session(
        circuit_key=circuit_key,
        is_cancelled=False,
        meeting_key=meeting_key,
        session_key=session_key,
        session_type="Race",
        year=2024,
    )


def _make_qual_session(session_key: int = 2, meeting_key: int = 100) -> Session:
    return Session(
        circuit_key=6,
        is_cancelled=False,
        meeting_key=meeting_key,
        session_key=session_key,
        session_type="Qualifying",
        year=2024,
    )


def _make_lap(
    driver_number: int = 1,
    lap_number: int = 5,
    lap_duration: float | None = 90.0,
    is_pit_out_lap: bool | None = False,
    session_key: int = 1,
    meeting_key: int = 100,
    duration_sector_1: float | None = 30.0,
    duration_sector_2: float | None = 30.0,
    duration_sector_3: float | None = 30.0,
) -> Lap:
    return Lap(
        driver_number=driver_number,
        lap_number=lap_number,
        lap_duration=lap_duration,
        is_pit_out_lap=is_pit_out_lap,
        session_key=session_key,
        meeting_key=meeting_key,
        duration_sector_1=duration_sector_1,
        duration_sector_2=duration_sector_2,
        duration_sector_3=duration_sector_3,
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
        stint_number=1,
    )


def _make_grid_entry(
    driver_number: int = 1,
    position: int = 5,
    session_key: int = 2,
    meeting_key: int = 100,
) -> StartingGridEntry:
    return StartingGridEntry(
        driver_number=driver_number,
        position=position,
        session_key=session_key,
        meeting_key=meeting_key,
    )


def _make_session_result(
    driver_number: int = 1,
    position: int | None = 3,
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
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_driver_pace_profile_standard() -> None:
    """Basic call with mocked data returns a DriverPaceProfile with correct driver_number."""
    client = MagicMock()

    qual_session = _make_qual_session(session_key=2, meeting_key=100)
    race_session = _make_session(session_key=1, meeting_key=100)
    grid_entry = _make_grid_entry(driver_number=1, position=5, session_key=2)
    # Laps with tyre age in 3-15 window: lap_number=5, stint starts lap 1, tyre_age_at_start=0
    # tyre_age = 5 - 1 + 0 = 4 → in window
    driver_lap = _make_lap(driver_number=1, lap_number=5, lap_duration=90.0, session_key=1)
    other_lap = _make_lap(driver_number=2, lap_number=5, lap_duration=92.0, session_key=1)
    stint = _make_stint(driver_number=1, lap_start=1, lap_end=50, tyre_age_at_start=0, session_key=1)
    race_result = _make_session_result(driver_number=1, position=3, session_key=1)
    race_grid = _make_grid_entry(driver_number=1, position=5, session_key=1)

    async def fake_get(path: str, model: type, **filters: object) -> list:
        sk = filters.get("session_key")
        dn = filters.get("driver_number")
        if path == "meetings":
            from lapwise.models.meetings import Meeting
            from datetime import datetime
            return [
                Meeting(
                    circuit_key=6,
                    is_cancelled=False,
                    meeting_key=100,
                    year=2024,
                    date_start=datetime(2024, 5, 1),
                )
            ]
        if path == "sessions" and filters.get("meeting_key") == 100:
            return [qual_session, race_session]
        if path == "starting_grid" and sk == 2:
            return [grid_entry]
        if path == "starting_grid" and sk == 1:
            return [race_grid]
        if path == "laps" and sk == 2:
            return [
                _make_lap(driver_number=1, session_key=2, duration_sector_1=28.0),
                _make_lap(driver_number=2, session_key=2, duration_sector_1=27.5),
            ]
        if path == "laps" and sk == 1 and dn == 1:
            return [driver_lap]
        if path == "laps" and sk == 1 and dn is None:
            return [driver_lap, other_lap]
        if path == "stints" and sk == 1 and dn == 1:
            return [stint]
        if path == "stints" and sk == 1 and dn == 2:
            return [_make_stint(driver_number=2, session_key=1)]
        if path == "session_result" and sk == 1:
            return [race_result]
        return []

    client.get = AsyncMock(side_effect=fake_get)

    service = DriverPaceService(client)
    result = await service.get_driver_pace_profile(driver_number=1, last_n_races=5)

    assert isinstance(result, DriverPaceProfile)
    assert result.driver_number == 1
    assert result.sample_races == 1
    assert result.qpace_score >= 0.0
    assert result.qpace_trend in ("IMPROVING", "DECLINING", "STABLE")


@pytest.mark.asyncio
async def test_driver_pace_profile_insufficient_clean_laps() -> None:
    """When no laps pass the prime-window tyre filter, rpace_score is None."""
    client = MagicMock()

    race_session = _make_session(session_key=1, meeting_key=100)
    qual_session = _make_qual_session(session_key=2, meeting_key=100)
    # Stint starts at lap 1 with tyre_age_at_start=0.
    # Driver's only lap is lap 2 → tyre_age = 2 - 1 + 0 = 1 → outside [3, 15] window.
    driver_lap = _make_lap(driver_number=1, lap_number=2, lap_duration=90.0, session_key=1)
    other_lap = _make_lap(driver_number=2, lap_number=2, lap_duration=90.0, session_key=1)
    stint = _make_stint(driver_number=1, lap_start=1, tyre_age_at_start=0, session_key=1)
    grid_entry = _make_grid_entry(driver_number=1, position=10, session_key=2)

    async def fake_get(path: str, model: type, **filters: object) -> list:
        sk = filters.get("session_key")
        dn = filters.get("driver_number")
        if path == "meetings":
            from lapwise.models.meetings import Meeting
            from datetime import datetime
            return [
                Meeting(
                    circuit_key=6,
                    is_cancelled=False,
                    meeting_key=100,
                    year=2024,
                    date_start=datetime(2024, 5, 1),
                )
            ]
        if path == "sessions" and filters.get("meeting_key") == 100:
            return [qual_session, race_session]
        if path == "starting_grid" and sk == 2:
            return [grid_entry]
        if path == "starting_grid" and sk == 1:
            return [_make_grid_entry(driver_number=1, position=10, session_key=1)]
        if path == "laps" and sk == 2:
            return []
        if path == "laps" and sk == 1 and dn == 1:
            return [driver_lap]
        if path == "laps" and sk == 1 and dn is None:
            return [driver_lap, other_lap]
        if path == "stints" and sk == 1:
            return [stint]
        if path == "session_result":
            return [_make_session_result(driver_number=1, position=10, session_key=1)]
        return []

    client.get = AsyncMock(side_effect=fake_get)

    service = DriverPaceService(client)
    result = await service.get_driver_pace_profile(driver_number=1, last_n_races=5)

    assert result.rpace_score is None
    assert result.rpace_percentile is None


@pytest.mark.asyncio
async def test_driver_pace_profile_driver_absent_from_session() -> None:
    """Driver not in the starting grid for a session contributes 0 to qpace_score."""
    client = MagicMock()

    qual_session = _make_qual_session(session_key=2, meeting_key=100)
    # Grid has only driver 2 — driver 1 is absent
    grid_entry_other = _make_grid_entry(driver_number=2, position=1, session_key=2)

    async def fake_get(path: str, model: type, **filters: object) -> list:
        sk = filters.get("session_key")
        if path == "meetings":
            from lapwise.models.meetings import Meeting
            from datetime import datetime
            return [
                Meeting(
                    circuit_key=6,
                    is_cancelled=False,
                    meeting_key=100,
                    year=2024,
                    date_start=datetime(2024, 5, 1),
                )
            ]
        if path == "sessions" and filters.get("meeting_key") == 100:
            return [qual_session]
        if path == "starting_grid" and sk == 2:
            return [grid_entry_other]
        return []

    client.get = AsyncMock(side_effect=fake_get)

    service = DriverPaceService(client)
    result = await service.get_driver_pace_profile(driver_number=1, last_n_races=5)

    # With score=0 for the only session, qpace_score should be 0
    assert result.qpace_score == 0.0
    assert result.driver_number == 1


@pytest.mark.asyncio
async def test_driver_pace_profile_circuit_history_fetches_extra_meetings() -> None:
    """When include_circuit_history=True and session_key provided, circuit meeting filters are used."""
    client = MagicMock()

    target_session = Session(
        circuit_key=16,
        is_cancelled=False,
        meeting_key=200,
        session_key=999,
        session_type="Race",
        year=2024,
    )

    get_last_n_mock = AsyncMock(return_value=[200])
    get_sessions_mock = AsyncMock(return_value=[])

    async def fake_get(path: str, model: type, **filters: object) -> list:
        if path == "sessions" and filters.get("session_key") == 999:
            return [target_session]
        return []

    client.get = AsyncMock(side_effect=fake_get)

    with (
        patch(
            "lapwise.services.analysis.driver_pace.get_last_n_meeting_keys",
            get_last_n_mock,
        ),
        patch(
            "lapwise.services.analysis.driver_pace.get_sessions_for_meetings",
            get_sessions_mock,
        ),
    ):
        service = DriverPaceService(client)
        result = await service.get_driver_pace_profile(
            driver_number=1,
            last_n_races=10,
            session_key=999,
            include_circuit_history=True,
        )

    # Verify get_last_n_meeting_keys was called with circuit_key and year_range
    get_last_n_mock.assert_called_once()
    call_kwargs = get_last_n_mock.call_args
    assert call_kwargs.kwargs.get("circuit_key") == 16 or (
        len(call_kwargs.args) > 2 and call_kwargs.args[2] == 16
    )

    assert isinstance(result, DriverPaceProfile)
    assert result.driver_number == 1
