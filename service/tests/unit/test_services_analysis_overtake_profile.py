"""Unit tests for OvertakeProfileService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.analysis.overtake_profile import OvertakeProfile
from lapwise.models.overtakes import Overtake
from lapwise.models.sessions import Session
from lapwise.services.analysis.overtake_profile import OvertakeProfileService


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_session(
    session_key: int,
    meeting_key: int,
    session_type: str = "Race",
    circuit_key: int = 10,
    is_cancelled: bool = False,
) -> Session:
    return Session(
        session_key=session_key,
        meeting_key=meeting_key,
        session_type=session_type,
        circuit_key=circuit_key,
        is_cancelled=is_cancelled,
        year=2024,
    )


def _make_overtake(
    overtaking: int,
    overtaken: int,
    session_key: int = 9001,
    meeting_key: int = 1219,
) -> Overtake:
    return Overtake(
        date=datetime(2024, 3, 24, 14, 30, 0),
        meeting_key=meeting_key,
        overtaking_driver_number=overtaking,
        overtaken_driver_number=overtaken,
        position=5,
        session_key=session_key,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overtake_profile_all_drivers() -> None:
    """Returns profiles for all drivers appearing in overtake data with correct counts."""
    client = MagicMock()

    meeting_keys = [1219]
    sessions = [_make_session(session_key=9001, meeting_key=1219)]
    overtakes = [
        _make_overtake(overtaking=1, overtaken=44, session_key=9001),
        _make_overtake(overtaking=1, overtaken=16, session_key=9001),
        _make_overtake(overtaking=44, overtaken=63, session_key=9001),
    ]

    with (
        patch(
            "lapwise.services.analysis.overtake_profile.get_last_n_meeting_keys",
            new=AsyncMock(return_value=meeting_keys),
        ),
        patch(
            "lapwise.services.analysis.overtake_profile.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = AsyncMock(return_value=overtakes)

        service = OvertakeProfileService(client)
        profiles = await service.get_overtake_profiles()

    assert len(profiles) == 4  # drivers: 1, 44, 16, 63

    by_driver = {p.driver_number: p for p in profiles}

    # Driver 1: made 2, lost 0
    assert by_driver[1].overtakes_made == 2
    assert by_driver[1].overtakes_lost == 0
    assert by_driver[1].net_overtakes == 2

    # Driver 44: made 1, lost 1
    assert by_driver[44].overtakes_made == 1
    assert by_driver[44].overtakes_lost == 1
    assert by_driver[44].net_overtakes == 0

    # total_races == number of sessions (1 Race session)
    for p in profiles:
        assert p.total_races == 1
        assert p.sample_races == 1


@pytest.mark.asyncio
async def test_overtake_profile_single_driver() -> None:
    """When driver_number is provided, only one entry is returned for that driver."""
    client = MagicMock()

    meeting_keys = [1219]
    sessions = [_make_session(session_key=9001, meeting_key=1219)]
    overtakes = [
        _make_overtake(overtaking=1, overtaken=44, session_key=9001),
        _make_overtake(overtaking=44, overtaken=16, session_key=9001),
    ]

    with (
        patch(
            "lapwise.services.analysis.overtake_profile.get_last_n_meeting_keys",
            new=AsyncMock(return_value=meeting_keys),
        ),
        patch(
            "lapwise.services.analysis.overtake_profile.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = AsyncMock(return_value=overtakes)

        service = OvertakeProfileService(client)
        profiles = await service.get_overtake_profiles(driver_number=44)

    assert len(profiles) == 1
    assert profiles[0].driver_number == 44
    assert profiles[0].overtakes_made == 1
    assert profiles[0].overtakes_lost == 1


@pytest.mark.asyncio
async def test_overtake_profile_zero_overtakes() -> None:
    """A driver who made no overtakes gets overtakes_made=0 and aggression_score=0."""
    client = MagicMock()

    meeting_keys = [1219]
    sessions = [_make_session(session_key=9001, meeting_key=1219)]
    # Only driver 1 made an overtake; driver 44 was only overtaken
    overtakes = [
        _make_overtake(overtaking=1, overtaken=44, session_key=9001),
    ]

    with (
        patch(
            "lapwise.services.analysis.overtake_profile.get_last_n_meeting_keys",
            new=AsyncMock(return_value=meeting_keys),
        ),
        patch(
            "lapwise.services.analysis.overtake_profile.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = AsyncMock(return_value=overtakes)

        service = OvertakeProfileService(client)
        profiles = await service.get_overtake_profiles()

    by_driver = {p.driver_number: p for p in profiles}

    # Driver 44 was only overtaken, never made an overtake
    assert by_driver[44].overtakes_made == 0
    assert by_driver[44].overtake_rate == 0.0
    assert by_driver[44].aggression_score == 0.0

    # Driver 1 made one overtake and should have the top aggression score (100)
    assert by_driver[1].overtakes_made == 1
    assert by_driver[1].aggression_score == 100.0


@pytest.mark.asyncio
async def test_overtake_profile_sprint_weekend_session_count() -> None:
    """Two sessions (Race + Sprint) in one weekend count as total_races=2."""
    client = MagicMock()

    meeting_keys = [1219]
    # One weekend with both Race and Sprint sessions
    sessions = [
        _make_session(session_key=9001, meeting_key=1219, session_type="Race"),
        _make_session(session_key=9002, meeting_key=1219, session_type="Sprint"),
    ]
    # Each session has its own overtake record; service fetches per-session
    overtakes_by_session: dict[int, list[Overtake]] = {
        9001: [_make_overtake(overtaking=1, overtaken=44, session_key=9001)],
        9002: [_make_overtake(overtaking=1, overtaken=16, session_key=9002)],
    }

    async def mock_client_get(path: str, model: type, **kwargs: object) -> list:
        sk = kwargs.get("session_key")
        if path == "overtakes" and sk is not None:
            return overtakes_by_session.get(int(sk), [])  # type: ignore[return-value]
        return []

    with (
        patch(
            "lapwise.services.analysis.overtake_profile.get_last_n_meeting_keys",
            new=AsyncMock(return_value=meeting_keys),
        ),
        patch(
            "lapwise.services.analysis.overtake_profile.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = mock_client_get

        service = OvertakeProfileService(client)
        profiles = await service.get_overtake_profiles()

    # total_races should be 2 (Race + Sprint), even though sample_races=1 (one weekend)
    for p in profiles:
        assert p.total_races == 2
        assert p.sample_races == 1

    by_driver = {p.driver_number: p for p in profiles}
    # Driver 1 made 2 overtakes across 2 sessions → overtake_rate = 1.0
    assert by_driver[1].overtakes_made == 2
    assert by_driver[1].overtake_rate == pytest.approx(1.0)
