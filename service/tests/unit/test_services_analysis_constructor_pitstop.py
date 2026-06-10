"""Unit tests for ConstructorPitstopService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.analysis.constructor_pitstop import ConstructorPitstop
from lapwise.models.drivers import Driver
from lapwise.models.meetings import Meeting
from lapwise.models.pit import PitStop
from lapwise.models.sessions import Session
from lapwise.services.analysis.constructor_pitstop import ConstructorPitstopService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MEETING_KEY = 1000
_SESSION_KEY = 2000


def _make_meeting(**overrides: object) -> Meeting:
    defaults: dict[str, object] = {
        "circuit_key": 10,
        "meeting_key": _MEETING_KEY,
        "year": 2024,
        "is_cancelled": False,
        "date_start": "2024-03-10T00:00:00+00:00",
        "date_end": "2024-03-12T00:00:00+00:00",
    }
    defaults.update(overrides)
    return Meeting(**defaults)


def _make_session(**overrides: object) -> Session:
    defaults: dict[str, object] = {
        "circuit_key": 10,
        "meeting_key": _MEETING_KEY,
        "session_key": _SESSION_KEY,
        "session_type": "Race",
        "is_cancelled": False,
        "year": 2024,
    }
    defaults.update(overrides)
    return Session(**defaults)


def _make_driver(driver_number: int, team_name: str, **overrides: object) -> Driver:
    defaults: dict[str, object] = {
        "driver_number": driver_number,
        "team_name": team_name,
        "meeting_key": _MEETING_KEY,
        "session_key": _SESSION_KEY,
    }
    defaults.update(overrides)
    return Driver(**defaults)


def _make_pit(
    driver_number: int,
    stop_duration: float | None,
    lane_duration: float | None = 22.0,
    **overrides: object,
) -> PitStop:
    defaults: dict[str, object] = {
        "date": "2024-03-10T14:30:00+00:00",
        "driver_number": driver_number,
        "lane_duration": lane_duration,
        "lap_number": 20,
        "meeting_key": _MEETING_KEY,
        "session_key": _SESSION_KEY,
        "stop_duration": stop_duration,
        "pit_duration": lane_duration,
    }
    defaults.update(overrides)
    return PitStop(**defaults)


def _build_client(
    meetings: list[Meeting],
    sessions: list[Session],
    pit_stops: list[PitStop],
    drivers: list[Driver],
) -> MagicMock:
    """Return a mock OpenF1Client whose .get() dispatches by endpoint path."""

    async def _get(path: str, model: type, **filters: object) -> list:
        if path == "meetings":
            return meetings
        if path == "sessions":
            return sessions
        if path == "pit":
            sk = filters.get("session_key")
            return [p for p in pit_stops if p.session_key == sk]
        if path == "drivers":
            sk = filters.get("session_key")
            return [d for d in drivers if d.session_key == sk]
        return []

    client = MagicMock()
    client.get = AsyncMock(side_effect=_get)
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_constructor_pitstop_all_constructors() -> None:
    """Returns entries for every constructor that has valid stops in the sample."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [
        _make_driver(1, "Red Bull Racing"),
        _make_driver(44, "Mercedes"),
    ]
    pit_stops = [
        _make_pit(1, 2.3),
        _make_pit(44, 2.8),
    ]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results: list[ConstructorPitstop] = await service.get_constructor_pitstops(last_n_races=1)

    team_names = {r.team_name for r in results}
    assert "Red Bull Racing" in team_names
    assert "Mercedes" in team_names
    assert len(results) == 2


@pytest.mark.asyncio
async def test_constructor_pitstop_single_constructor() -> None:
    """team_name filter returns only that constructor's data."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [
        _make_driver(1, "Red Bull Racing"),
        _make_driver(44, "Mercedes"),
    ]
    pit_stops = [
        _make_pit(1, 2.3),
        _make_pit(44, 2.8),
    ]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results = await service.get_constructor_pitstops(team_name="Mercedes", last_n_races=1)

    assert len(results) == 1
    assert results[0].team_name == "Mercedes"


@pytest.mark.asyncio
async def test_constructor_pitstop_null_stop_duration_excluded() -> None:
    """Stops with stop_duration=None are excluded from sample_stops."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [_make_driver(1, "Ferrari")]
    # One valid stop, one null stop
    pit_stops = [
        _make_pit(1, 2.4),
        _make_pit(1, None),
    ]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results = await service.get_constructor_pitstops(last_n_races=1)

    assert len(results) == 1
    assert results[0].sample_stops == 1  # only the valid stop


@pytest.mark.asyncio
async def test_constructor_pitstop_outlier_excluded() -> None:
    """Stops with stop_duration > 60s are excluded (outlier filter)."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [_make_driver(16, "Ferrari")]
    pit_stops = [
        _make_pit(16, 2.1),
        _make_pit(16, 120.0),  # outlier
    ]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results = await service.get_constructor_pitstops(last_n_races=1)

    assert len(results) == 1
    ferrari = results[0]
    assert ferrari.sample_stops == 1
    assert ferrari.fastest_stop_in_sample == pytest.approx(2.1)


@pytest.mark.asyncio
async def test_constructor_pitstop_tied_fastest_pitstop() -> None:
    """Two constructors with the same session field_min both get fastest_pitstop_rate credit."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [
        _make_driver(1, "Red Bull Racing"),
        _make_driver(63, "Mercedes"),
    ]
    # Both record the exact same minimum stop duration
    shared_min = 1.9
    pit_stops = [
        _make_pit(1, shared_min),
        _make_pit(63, shared_min),
    ]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results = await service.get_constructor_pitstops(last_n_races=1)

    assert len(results) == 2
    for r in results:
        assert r.fastest_pitstop_rate == pytest.approx(1.0), (
            f"{r.team_name} should get fastest_pitstop_rate=1.0 on a tie"
        )


@pytest.mark.asyncio
async def test_constructor_pitstop_sub_2s_scoring() -> None:
    """A stop < 2.0s earns 20 bracket points and is counted in sub_2s_rate."""
    meetings = [_make_meeting()]
    sessions = [_make_session()]
    drivers = [_make_driver(55, "Ferrari")]
    # One sub-2s stop
    pit_stops = [_make_pit(55, 1.95)]
    client = _build_client(meetings, sessions, pit_stops, drivers)

    service = ConstructorPitstopService(client)
    results = await service.get_constructor_pitstops(last_n_races=1)

    assert len(results) == 1
    ferrari = results[0]

    # sub_2s_rate: 1 out of 1 stop
    assert ferrari.sub_2s_rate == pytest.approx(1.0)

    # fantasy_points: bracket=20, fastest bonus=+5 (only constructor) → 25
    assert ferrari.fantasy_points_avg == pytest.approx(25.0)
