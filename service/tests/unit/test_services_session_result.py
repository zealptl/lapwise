"""Unit tests for SessionResultService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.session_result import SessionResult
from lapwise.services.session_result import SessionResultService


def _make_result(**overrides: object) -> SessionResult:
    defaults: dict[str, object] = {
        "dnf": False,
        "dns": False,
        "dsq": False,
        "driver_number": 1,
        "duration": 5412.234,
        "gap_to_leader": None,
        "number_of_laps": 53,
        "meeting_key": 1219,
        "position": 1,
        "session_key": 9161,
    }
    defaults.update(overrides)
    return SessionResult(**defaults)


@pytest.mark.asyncio
async def test_list_results_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_result()]
    client.get = AsyncMock(return_value=expected)

    service = SessionResultService(client)
    result = await service.list_results(session_key=9161, position_lte=3)

    client.get.assert_called_once_with(
        "session_result",
        SessionResult,
        session_key=9161,
        position_lte=3,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_results_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = SessionResultService(client)
    result = await service.list_results()

    assert result == []
