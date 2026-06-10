"""Unit tests for DnfRatesService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lapwise.models.analysis.dnf_rates import DnfRates
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.services.analysis.dnf_rates import DnfRatesService


def _make_session(
    session_key: int,
    meeting_key: int,
    session_type: str,
    is_cancelled: bool = False,
) -> Session:
    return Session(
        circuit_key=1,
        circuit_short_name="Test",
        country_code="TST",
        country_key=1,
        country_name="Testland",
        date_end=None,
        date_start=None,
        gmt_offset="00:00:00",
        is_cancelled=is_cancelled,
        location="Test Circuit",
        meeting_key=meeting_key,
        session_key=session_key,
        session_name=session_type,
        session_type=session_type,
        year=2024,
    )


def _make_result(
    driver_number: int,
    session_key: int,
    meeting_key: int,
    dnf: bool = False,
    dns: bool = False,
    dsq: bool = False,
) -> SessionResult:
    return SessionResult(
        driver_number=driver_number,
        session_key=session_key,
        meeting_key=meeting_key,
        dnf=dnf,
        dns=dns,
        dsq=dsq,
    )


@pytest.mark.asyncio
async def test_dnf_rates_all_drivers() -> None:
    """Returns a list of DnfRates with an entry for each driver seen across sessions."""
    client = MagicMock()

    sessions = [
        _make_session(101, 1, "Race"),
        _make_session(102, 1, "Qualifying"),
    ]
    # Two drivers in Race, one DNF; same two in Qualifying, both clean
    results_by_session = {
        101: [
            _make_result(1, 101, 1, dnf=True),
            _make_result(44, 101, 1),
        ],
        102: [
            _make_result(1, 102, 1),
            _make_result(44, 102, 1),
        ],
    }

    with (
        patch(
            "lapwise.services.analysis.dnf_rates.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[1]),
        ),
        patch(
            "lapwise.services.analysis.dnf_rates.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        async def fake_get(path: str, model: type, **kwargs: object) -> list:
            sk = kwargs.get("session_key")
            return results_by_session.get(sk, [])  # type: ignore[arg-type]

        client.get = AsyncMock(side_effect=fake_get)
        service = DnfRatesService(client)
        result = await service.get_dnf_rates()

    assert isinstance(result, list)
    assert len(result) == 2
    driver_nums = {r.driver_number for r in result}
    assert driver_nums == {1, 44}

    driver1 = next(r for r in result if r.driver_number == 1)
    assert driver1.dnf_count == 1
    assert driver1.total_sessions == 2
    assert driver1.dnf_rate == pytest.approx(0.5)
    assert driver1.reliability_score == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_dnf_rates_single_driver() -> None:
    """When driver_number is provided, only that driver's stats are returned."""
    client = MagicMock()

    sessions = [_make_session(101, 1, "Race")]
    results = [
        _make_result(1, 101, 1, dnf=True),
        _make_result(44, 101, 1),
    ]

    with (
        patch(
            "lapwise.services.analysis.dnf_rates.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[1]),
        ),
        patch(
            "lapwise.services.analysis.dnf_rates.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = AsyncMock(return_value=results)
        service = DnfRatesService(client)
        result = await service.get_dnf_rates(driver_number=1)

    assert len(result) == 1
    assert result[0].driver_number == 1
    assert result[0].dnf_count == 1


@pytest.mark.asyncio
async def test_dnf_rates_zero_dnfs() -> None:
    """A driver with no incidents gets reliability_score=100 and dnf_rate=0."""
    client = MagicMock()

    sessions = [_make_session(101, 1, "Race")]
    results = [_make_result(33, 101, 1, dnf=False, dns=False, dsq=False)]

    with (
        patch(
            "lapwise.services.analysis.dnf_rates.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[1]),
        ),
        patch(
            "lapwise.services.analysis.dnf_rates.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        client.get = AsyncMock(return_value=results)
        service = DnfRatesService(client)
        result = await service.get_dnf_rates(driver_number=33)

    assert len(result) == 1
    entry = result[0]
    assert entry.dnf_count == 0
    assert entry.dns_count == 0
    assert entry.dsq_count == 0
    assert entry.dnf_rate == pytest.approx(0.0)
    assert entry.reliability_score == pytest.approx(100.0)


@pytest.mark.asyncio
async def test_dnf_rates_sprint_inclusion() -> None:
    """Sprint session DNF is counted in the sprint_dnf_rate breakdown field."""
    client = MagicMock()

    sessions = [
        _make_session(101, 1, "Race"),
        _make_session(102, 1, "Sprint"),
    ]
    results_by_session = {
        101: [_make_result(16, 101, 1, dnf=False)],
        102: [_make_result(16, 102, 1, dnf=True)],
    }

    with (
        patch(
            "lapwise.services.analysis.dnf_rates.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[1]),
        ),
        patch(
            "lapwise.services.analysis.dnf_rates.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        async def fake_get(path: str, model: type, **kwargs: object) -> list:
            sk = kwargs.get("session_key")
            return results_by_session.get(sk, [])  # type: ignore[arg-type]

        client.get = AsyncMock(side_effect=fake_get)
        service = DnfRatesService(client)
        result = await service.get_dnf_rates(driver_number=16)

    assert len(result) == 1
    entry = result[0]
    assert entry.breakdown.sprint_dnf_rate == pytest.approx(1.0)
    assert entry.breakdown.race_dnf_rate == pytest.approx(0.0)
    assert entry.dnf_count == 1
    assert entry.total_sessions == 2


@pytest.mark.asyncio
async def test_dnf_rates_absent_driver() -> None:
    """A driver absent from a session's results doesn't have that session counted."""
    client = MagicMock()

    # Two sessions; driver 55 only appears in the second one
    sessions = [
        _make_session(101, 1, "Race"),
        _make_session(102, 1, "Qualifying"),
    ]
    results_by_session = {
        101: [_make_result(1, 101, 1)],  # driver 55 absent
        102: [_make_result(55, 102, 1, dnf=True)],  # driver 55 present, DNF
    }

    with (
        patch(
            "lapwise.services.analysis.dnf_rates.get_last_n_meeting_keys",
            new=AsyncMock(return_value=[1]),
        ),
        patch(
            "lapwise.services.analysis.dnf_rates.get_sessions_for_meetings",
            new=AsyncMock(return_value=sessions),
        ),
    ):
        async def fake_get(path: str, model: type, **kwargs: object) -> list:
            sk = kwargs.get("session_key")
            return results_by_session.get(sk, [])  # type: ignore[arg-type]

        client.get = AsyncMock(side_effect=fake_get)
        service = DnfRatesService(client)
        result = await service.get_dnf_rates(driver_number=55)

    assert len(result) == 1
    entry = result[0]
    # Only 1 session counted (the qualifying where driver 55 has a result)
    assert entry.total_sessions == 1
    assert entry.dnf_count == 1
    assert entry.dnf_rate == pytest.approx(1.0)
