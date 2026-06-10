"""Unit tests for ChampionshipContextService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.championship import ChampionshipDriver, ChampionshipTeam
from lapwise.models.drivers import Driver
from lapwise.models.meetings import Meeting
from lapwise.services.analysis.championship_context import ChampionshipContextService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _meeting(meeting_key: int, date_start: datetime | None = None) -> Meeting:
    return Meeting(
        circuit_key=1,
        is_cancelled=False,
        meeting_key=meeting_key,
        year=2024,
        date_start=date_start or datetime(2024, 1, meeting_key),
    )


def _champ_driver(
    driver_number: int,
    position_current: int,
    points_current: float,
    points_start: float = 0.0,
    meeting_key: int = 100,
) -> ChampionshipDriver:
    return ChampionshipDriver(
        driver_number=driver_number,
        meeting_key=meeting_key,
        points_current=points_current,
        points_start=points_start,
        position_current=position_current,
        position_start=position_current,
        session_key=9000 + meeting_key,
    )


def _champ_team(
    team_name: str,
    position_current: int,
    points_current: float,
    meeting_key: int = 100,
) -> ChampionshipTeam:
    return ChampionshipTeam(
        team_name=team_name,
        meeting_key=meeting_key,
        points_current=points_current,
        points_start=0.0,
        position_current=position_current,
        position_start=position_current,
        session_key=9000 + meeting_key,
    )


def _driver(driver_number: int, team_name: str, meeting_key: int = 100) -> Driver:
    return Driver(
        driver_number=driver_number,
        team_name=team_name,
        full_name=f"Driver {driver_number}",
        session_key=9000 + meeting_key,
        meeting_key=meeting_key,
    )


def _make_client(
    meetings: list[Meeting],
    latest_drivers: list[ChampionshipDriver],
    last_3_drivers: list[list[ChampionshipDriver]] | None = None,
    teams: list[ChampionshipTeam] | None = None,
    drivers: list[Driver] | None = None,
) -> MagicMock:
    """Build a mock OpenF1Client whose .get() responds based on path."""
    client = MagicMock()

    # last_3_drivers defaults to repeating latest_drivers for each of the last 3 meetings
    if last_3_drivers is None:
        last_3_drivers = [latest_drivers] * min(3, len(meetings))

    if teams is None:
        teams = []

    if drivers is None:
        drivers = []

    # We need get() to be side-effectful based on call arguments.
    # Track call order: meetings first, then championship_drivers (latest),
    # then championship_drivers * 3 (last 3), then championship_teams, then drivers.
    call_responses: list = (
        [meetings]
        + [latest_drivers]
        + last_3_drivers
        + [teams]
        + [drivers]
    )
    call_iter = iter(call_responses)

    async def _get(path: str, model: type, **kwargs):  # type: ignore[no-untyped-def]
        return next(call_iter)

    client.get = _get
    return client


# ---------------------------------------------------------------------------
# Test 1: championship leader has points_gap_to_leader=0 and desperation_index=0
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_championship_leader_zero_gap() -> None:
    """P1 driver should have points_gap_to_leader=0 and desperation_index=0."""
    meetings = [_meeting(100, datetime(2024, 3, 1))]
    leader = _champ_driver(1, 1, 331.0, points_start=300.0)
    second = _champ_driver(11, 2, 280.0, points_start=250.0)
    team_a = _champ_team("Red Bull Racing", 1, 500.0)
    team_b = _champ_team("Ferrari", 2, 400.0)
    d1 = _driver(1, "Red Bull Racing")
    d11 = _driver(11, "Ferrari")

    client = _make_client(
        meetings=meetings,
        latest_drivers=[leader, second],
        last_3_drivers=[[leader, second]],  # 1 meeting only
        teams=[team_a, team_b],
        drivers=[d1, d11],
    )

    service = ChampionshipContextService(client)
    result = await service.get_championship_context(season=2024)

    assert result.season == 2024
    p1_ctx = next(d for d in result.drivers if d.championship_position == 1)
    assert p1_ctx.driver_number == 1
    assert p1_ctx.points_gap_to_leader == 0.0
    assert p1_ctx.desperation_index == 0.0


# ---------------------------------------------------------------------------
# Test 2: positive momentum when last-3 avg > 120% of season avg
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_championship_positive_momentum() -> None:
    """Driver scoring above 120% of season avg should have momentum='POSITIVE'."""
    # 5 included meetings; driver has 50 pts total → season avg = 10 pts/race
    # Last 3 meetings: driver scores 20+20+20 = 60, avg = 20 → >120% of 10
    meetings = [_meeting(100 + i, datetime(2024, 1 + i, 1)) for i in range(5)]
    latest_key = 104

    # Latest standing: driver 1 has 50 pts at position 1
    latest_drivers = [_champ_driver(1, 1, 50.0, points_start=30.0, meeting_key=latest_key)]

    # Last 3 meetings show 20 pts scored each (points_current - points_start = 20)
    last_3_records = [
        [_champ_driver(1, 1, 50.0, points_start=30.0, meeting_key=104)],
        [_champ_driver(1, 1, 30.0, points_start=10.0, meeting_key=103)],
        [_champ_driver(1, 1, 10.0, points_start=-10.0, meeting_key=102)],
    ]

    teams = [_champ_team("Red Bull Racing", 1, 200.0, meeting_key=latest_key)]
    drivers = [_driver(1, "Red Bull Racing", meeting_key=latest_key)]

    client = _make_client(
        meetings=meetings,
        latest_drivers=latest_drivers,
        last_3_drivers=last_3_records,
        teams=teams,
        drivers=drivers,
    )

    service = ChampionshipContextService(client)
    result = await service.get_championship_context(season=2024)

    p1_ctx = next(d for d in result.drivers if d.championship_position == 1)
    assert p1_ctx.momentum == "POSITIVE"


# ---------------------------------------------------------------------------
# Test 3: constructor battle flag — two constructors within 30 pts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_championship_constructor_battle_flag() -> None:
    """Constructors within 30 pts of each other → both under_pressure=True."""
    meetings = [_meeting(100, datetime(2024, 3, 1))]
    leader = _champ_driver(1, 1, 200.0, meeting_key=100)
    second = _champ_driver(11, 2, 150.0, meeting_key=100)

    # Teams 25 pts apart → within 30
    team_a = _champ_team("Red Bull Racing", 1, 400.0)
    team_b = _champ_team("Ferrari", 2, 375.0)  # diff = 25

    d1 = _driver(1, "Red Bull Racing")
    d11 = _driver(11, "Ferrari")

    client = _make_client(
        meetings=meetings,
        latest_drivers=[leader, second],
        last_3_drivers=[[leader, second]],
        teams=[team_a, team_b],
        drivers=[d1, d11],
    )

    service = ChampionshipContextService(client)
    result = await service.get_championship_context(season=2024)

    rb_ctx = next(c for c in result.constructors if c.team_name == "Red Bull Racing")
    ferrari_ctx = next(c for c in result.constructors if c.team_name == "Ferrari")
    assert rb_ctx.under_pressure is True
    assert ferrari_ctx.under_pressure is True

    # Driver belonging to Red Bull should have constructor_battle=True
    d1_ctx = next(d for d in result.drivers if d.championship_position == 1)
    assert d1_ctx.constructor_battle is True


# ---------------------------------------------------------------------------
# Test 4: after_round filter — only meetings up to the given key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_championship_after_round_filter() -> None:
    """When after_round is provided, only meetings with meeting_key <= after_round
    are included; desperation index is computed against those meetings only."""
    # 5 meetings, after_round=102 → only 3 meetings included
    meetings = [_meeting(100 + i, datetime(2024, 1 + i, 1)) for i in range(5)]

    # Provide responses for: meetings fetch → driver latest (key 102) →
    # last 3 (keys 102, 101, 100) → teams → drivers
    latest_key = 102
    latest_drivers = [
        _champ_driver(1, 1, 75.0, points_start=50.0, meeting_key=latest_key),
        _champ_driver(11, 2, 50.0, points_start=25.0, meeting_key=latest_key),
    ]
    last_3 = [
        [_champ_driver(1, 1, 75.0, points_start=50.0, meeting_key=102),
         _champ_driver(11, 2, 50.0, points_start=25.0, meeting_key=102)],
        [_champ_driver(1, 1, 50.0, points_start=25.0, meeting_key=101),
         _champ_driver(11, 2, 25.0, points_start=0.0, meeting_key=101)],
        [_champ_driver(1, 1, 25.0, points_start=0.0, meeting_key=100),
         _champ_driver(11, 2, 0.0, points_start=0.0, meeting_key=100)],
    ]
    teams = [
        _champ_team("Red Bull Racing", 1, 300.0, meeting_key=latest_key),
        _champ_team("Ferrari", 2, 100.0, meeting_key=latest_key),
    ]
    drivers = [
        _driver(1, "Red Bull Racing", meeting_key=latest_key),
        _driver(11, "Ferrari", meeting_key=latest_key),
    ]

    client = _make_client(
        meetings=meetings,
        latest_drivers=latest_drivers,
        last_3_drivers=last_3,
        teams=teams,
        drivers=drivers,
    )

    service = ChampionshipContextService(client)
    result = await service.get_championship_context(season=2024, after_round=102)

    # 3 meetings included, 2 remaining → max_remaining = 2 * 26 = 52
    # driver 11 gap = 75 - 50 = 25 → desperation = 25/52 * 100 ≈ 48.08
    d11_ctx = next(d for d in result.drivers if d.driver_number == 11)
    assert d11_ctx.points_gap_to_leader == 25.0
    assert d11_ctx.desperation_index < 100.0

    # Leader gap is 0
    d1_ctx = next(d for d in result.drivers if d.championship_position == 1)
    assert d1_ctx.points_gap_to_leader == 0.0


# ---------------------------------------------------------------------------
# Test 5: mathematical elimination → desperation_index = 100
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_championship_mathematical_elimination() -> None:
    """When gap > max_remaining_points, desperation_index must be 100."""
    # 10 total meetings, all 10 included (remaining = 0 after last round)
    # Or: 10 total, 9 included → 1 remaining → max_remaining = 26
    # Driver 2 gap = 300 pts → clearly > 26 → eliminated
    meetings = [_meeting(100 + i, datetime(2024, 1 + i, 1)) for i in range(10)]
    latest_key = 109  # 10th meeting (index 9)

    latest_drivers = [
        _champ_driver(1, 1, 350.0, meeting_key=latest_key),
        _champ_driver(11, 2, 50.0, meeting_key=latest_key),  # gap = 300 >> 26
    ]
    last_3 = [
        [_champ_driver(1, 1, 350.0, points_start=330.0, meeting_key=109),
         _champ_driver(11, 2, 50.0, points_start=30.0, meeting_key=109)],
        [_champ_driver(1, 1, 330.0, points_start=310.0, meeting_key=108),
         _champ_driver(11, 2, 30.0, points_start=10.0, meeting_key=108)],
        [_champ_driver(1, 1, 310.0, points_start=290.0, meeting_key=107),
         _champ_driver(11, 2, 10.0, points_start=0.0, meeting_key=107)],
    ]
    teams = [
        _champ_team("Red Bull Racing", 1, 600.0, meeting_key=latest_key),
        _champ_team("Ferrari", 2, 100.0, meeting_key=latest_key),
    ]
    drivers = [
        _driver(1, "Red Bull Racing", meeting_key=latest_key),
        _driver(11, "Ferrari", meeting_key=latest_key),
    ]

    client = _make_client(
        meetings=meetings,
        latest_drivers=latest_drivers,
        last_3_drivers=last_3,
        teams=teams,
        drivers=drivers,
    )

    service = ChampionshipContextService(client)
    # after_round = 109 (9th meeting, 0-indexed), total = 10 → 1 remaining
    result = await service.get_championship_context(season=2024, after_round=109)

    d11_ctx = next(d for d in result.drivers if d.driver_number == 11)
    assert d11_ctx.desperation_index == 100.0
