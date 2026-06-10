"""Unit tests for CircuitProfileService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.laps import Lap
from lapwise.models.meetings import Meeting
from lapwise.models.overtakes import Overtake
from lapwise.models.sessions import Session
from lapwise.models.stints import Stint
from lapwise.models.weather import Weather
from lapwise.services.analysis.circuit_profile import CircuitProfileService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CIRCUIT_KEY = 6  # Monaco


def _make_meeting(meeting_key: int, year: int = 2024) -> Meeting:
    return Meeting(
        circuit_key=_CIRCUIT_KEY,
        is_cancelled=False,
        meeting_key=meeting_key,
        year=year,
        date_start=None,
        circuit_info_url=None,
        circuit_image=None,
        circuit_short_name="Monaco",
        circuit_type=None,
        country_code=None,
        country_flag=None,
        country_key=None,
        country_name=None,
        date_end=None,
        gmt_offset=None,
        location=None,
        meeting_name=None,
        meeting_official_name=None,
    )


def _make_session(session_key: int, meeting_key: int) -> Session:
    return Session(
        circuit_key=_CIRCUIT_KEY,
        circuit_short_name="Monaco",
        is_cancelled=False,
        meeting_key=meeting_key,
        session_key=session_key,
        session_type="Race",
        year=2024,
        country_code=None,
        country_key=None,
        country_name=None,
        date_end=None,
        date_start=None,
        gmt_offset=None,
        location=None,
        session_name="Race",
    )


def _make_overtake(session_key: int) -> Overtake:
    return Overtake(
        date="2024-05-26T14:00:00+00:00",
        meeting_key=1,
        overtaken_driver_number=2,
        overtaking_driver_number=1,
        position=1,
        session_key=session_key,
    )


def _make_lap(
    session_key: int,
    lap_number: int,
    lap_duration: float | None,
    driver_number: int = 1,
) -> Lap:
    return Lap(
        driver_number=driver_number,
        lap_number=lap_number,
        lap_duration=lap_duration,
        meeting_key=1,
        session_key=session_key,
        is_pit_out_lap=False,
    )


def _make_stint(
    session_key: int,
    driver_number: int,
    stint_number: int,
    compound: str | None = "MEDIUM",
) -> Stint:
    return Stint(
        compound=compound,
        driver_number=driver_number,
        lap_start=1,
        lap_end=20,
        meeting_key=1,
        session_key=session_key,
        stint_number=stint_number,
    )


def _make_weather(session_key: int, rainfall: int | None) -> Weather:
    return Weather(
        date="2024-05-26T14:00:00+00:00",
        meeting_key=1,
        session_key=session_key,
        rainfall=rainfall,
    )


def _build_client(
    meetings_per_year: list[list[Meeting]],
    sessions_per_meeting: list[list[Session]],
    overtakes_per_session: list[list[Overtake]],
    laps_per_session: list[list[Lap]],
    stints_per_session: list[list[Stint]],
    weather_per_session: list[list[Weather]],
) -> MagicMock:
    """Build a mock OpenF1Client whose `get` side-effects follow call order."""
    client = MagicMock()

    # We'll track calls to route them by (path, kwargs)
    meeting_queue = list(meetings_per_year)
    session_queue = list(sessions_per_meeting)
    overtake_queue = list(overtakes_per_session)
    lap_queue = list(laps_per_session)
    stint_queue = list(stints_per_session)
    weather_queue = list(weather_per_session)

    async def _get(path: str, model: type, **kwargs: object) -> list:  # type: ignore[type-arg]
        if path == "meetings":
            return meeting_queue.pop(0)
        if path == "sessions":
            return session_queue.pop(0)
        if path == "overtakes":
            return overtake_queue.pop(0)
        if path == "laps":
            return lap_queue.pop(0)
        if path == "stints":
            return stint_queue.pop(0)
        if path == "weather":
            return weather_queue.pop(0)
        return []

    client.get = AsyncMock(side_effect=_get)
    return client


# ---------------------------------------------------------------------------
# Test 1: Low-overtake circuit → overtake_difficulty = "HIGH"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_profile_low_overtake_circuit() -> None:
    """Avg < 15 overtakes per race → overtake_difficulty should be HIGH."""
    meetings = [_make_meeting(101, 2024), _make_meeting(102, 2023), _make_meeting(103, 2022)]

    # 3 years of meetings, one meeting per year (collapsed into separate get calls per year)
    meetings_per_year: list[list[Meeting]] = [
        [meetings[0]],  # year 2024
        [meetings[1]],  # year 2023
        [meetings[2]],  # year 2022
    ]

    # One race session per meeting
    sessions = [
        _make_session(201, 101),
        _make_session(202, 102),
        _make_session(203, 103),
    ]
    sessions_per_meeting = [[sessions[0]], [sessions[1]], [sessions[2]]]

    # 5 overtakes in session 201, 10 in 202, 8 in 203 → avg = 7.67 → HIGH
    overtakes_per_session = [
        [_make_overtake(201) for _ in range(5)],
        [_make_overtake(202) for _ in range(10)],
        [_make_overtake(203) for _ in range(8)],
    ]

    # Simple laps: all ~90s to keep SC logic straightforward
    laps_per_session = [
        [_make_lap(201, i, 90.0) for i in range(1, 11)],
        [_make_lap(202, i, 90.0) for i in range(1, 11)],
        [_make_lap(203, i, 90.0) for i in range(1, 11)],
    ]

    # 2 stints per driver, 2 drivers
    stints_per_session = [
        [
            _make_stint(201, 1, 1, "MEDIUM"),
            _make_stint(201, 1, 2, "HARD"),
            _make_stint(201, 2, 1, "MEDIUM"),
            _make_stint(201, 2, 2, "HARD"),
        ],
        [_make_stint(202, 1, 1, "MEDIUM"), _make_stint(202, 1, 2, "HARD")],
        [_make_stint(203, 1, 1, "MEDIUM"), _make_stint(203, 1, 2, "HARD")],
    ]

    # Dry weather
    weather_per_session = [
        [_make_weather(201, 0)],
        [_make_weather(202, 0)],
        [_make_weather(203, 0)],
    ]

    client = _build_client(
        meetings_per_year,
        sessions_per_meeting,
        overtakes_per_session,
        laps_per_session,
        stints_per_session,
        weather_per_session,
    )

    service = CircuitProfileService(client)
    profile = await service.get_circuit_profile(_CIRCUIT_KEY, last_n_years=3)

    assert profile.overtake_difficulty == "HIGH"
    assert profile.qualifying_importance == 100
    assert profile.avg_overtakes_per_race is not None
    assert profile.avg_overtakes_per_race < 15


# ---------------------------------------------------------------------------
# Test 2: High rainfall → weather_variability = "HIGH"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_profile_high_rainfall() -> None:
    """> 30% of weather records show rainfall → weather_variability should be HIGH."""
    meetings_per_year: list[list[Meeting]] = [
        [_make_meeting(201, 2024)],
        [_make_meeting(202, 2023)],
        [],  # no meeting this year
    ]

    sessions = [_make_session(301, 201), _make_session(302, 202)]
    sessions_per_meeting = [[sessions[0]], [sessions[1]], []]

    overtakes_per_session = [[_make_overtake(301)] * 20, [_make_overtake(302)] * 20]

    laps_per_session = [
        [_make_lap(301, i, 90.0) for i in range(1, 11)],
        [_make_lap(302, i, 90.0) for i in range(1, 11)],
    ]

    stints_per_session = [
        [_make_stint(301, 1, 1, "INTERMEDIATE")],
        [_make_stint(302, 1, 1, "WET")],
    ]

    # 7 out of 20 records = rainfall=1 → 35% → HIGH
    weather_per_session = [
        [_make_weather(301, 1)] * 4 + [_make_weather(301, 0)] * 6,
        [_make_weather(302, 1)] * 3 + [_make_weather(302, 0)] * 7,
    ]

    client = _build_client(
        meetings_per_year,
        sessions_per_meeting,
        overtakes_per_session,
        laps_per_session,
        stints_per_session,
        weather_per_session,
    )

    service = CircuitProfileService(client)
    profile = await service.get_circuit_profile(_CIRCUIT_KEY, last_n_years=3)

    assert profile.weather_variability == "HIGH"


# ---------------------------------------------------------------------------
# Test 3: Compound frequency ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_profile_compound_frequency_ordering() -> None:
    """The compound used most often should appear first in typical_compounds."""
    meetings_per_year: list[list[Meeting]] = [
        [_make_meeting(301, 2024)],
        [_make_meeting(302, 2023)],
        [],
    ]

    sessions = [_make_session(401, 301), _make_session(402, 302)]
    sessions_per_meeting = [[sessions[0]], [sessions[1]], []]

    overtakes_per_session = [[_make_overtake(401)] * 5, [_make_overtake(402)] * 5]

    laps_per_session = [
        [_make_lap(401, i, 85.0) for i in range(1, 6)],
        [_make_lap(402, i, 85.0) for i in range(1, 6)],
    ]

    # MEDIUM used 5 times, HARD used 2 times, SOFT used 1 time
    stints_per_session = [
        [
            _make_stint(401, 1, 1, "MEDIUM"),
            _make_stint(401, 1, 2, "MEDIUM"),
            _make_stint(401, 2, 1, "MEDIUM"),
            _make_stint(401, 2, 2, "HARD"),
        ],
        [
            _make_stint(402, 1, 1, "MEDIUM"),
            _make_stint(402, 1, 2, "MEDIUM"),
            _make_stint(402, 2, 1, "HARD"),
            _make_stint(402, 2, 2, "SOFT"),
        ],
    ]

    weather_per_session = [
        [_make_weather(401, 0)],
        [_make_weather(402, 0)],
    ]

    client = _build_client(
        meetings_per_year,
        sessions_per_meeting,
        overtakes_per_session,
        laps_per_session,
        stints_per_session,
        weather_per_session,
    )

    service = CircuitProfileService(client)
    profile = await service.get_circuit_profile(_CIRCUIT_KEY, last_n_years=3)

    assert len(profile.typical_compounds) >= 1
    assert profile.typical_compounds[0] == "MEDIUM", (
        f"Expected MEDIUM first, got {profile.typical_compounds}"
    )
    # HARD should come before SOFT
    if "HARD" in profile.typical_compounds and "SOFT" in profile.typical_compounds:
        hard_idx = profile.typical_compounds.index("HARD")
        soft_idx = profile.typical_compounds.index("SOFT")
        assert hard_idx < soft_idx


# ---------------------------------------------------------------------------
# Test 4: Insufficient data (< 2 race sessions) → derived fields None / 0
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_profile_insufficient_data() -> None:
    """Fewer than 2 race sessions → derived fields should be None or 0."""
    meetings_per_year: list[list[Meeting]] = [
        [_make_meeting(401, 2024)],
        [],
        [],
    ]

    # Only one race session found
    sessions_per_meeting = [[_make_session(501, 401)], [], []]

    # These should never be reached since we bail out early, but provide empty lists
    overtakes_per_session: list[list[Overtake]] = []
    laps_per_session: list[list[Lap]] = []
    stints_per_session: list[list[Stint]] = []
    weather_per_session: list[list[Weather]] = []

    client = _build_client(
        meetings_per_year,
        sessions_per_meeting,
        overtakes_per_session,
        laps_per_session,
        stints_per_session,
        weather_per_session,
    )

    service = CircuitProfileService(client)
    profile = await service.get_circuit_profile(_CIRCUIT_KEY, last_n_years=3)

    assert profile.race_sessions_found < 2
    assert profile.overtake_difficulty is None
    assert profile.avg_overtakes_per_race is None
    assert profile.qualifying_importance is None
    assert profile.safety_car_tendency is None
    assert profile.weather_variability is None
    assert profile.typical_compounds == []
    assert profile.fl_typical_lap is None
    assert profile.avg_pit_stops == 0.0
