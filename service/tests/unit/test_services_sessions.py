"""Unit tests for SessionService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lapwise.models.sessions import Session
from lapwise.services.sessions import SessionService


def _make_session(**overrides: object) -> Session:
    defaults = {
        "circuit_key": 7,
        "circuit_short_name": "Spa",
        "country_code": "BEL",
        "country_key": 16,
        "country_name": "Belgium",
        "date_end": None,
        "date_start": None,
        "gmt_offset": "02:00:00",
        "is_cancelled": False,
        "location": "Spa-Francorchamps",
        "meeting_key": 1216,
        "session_key": 9140,
        "session_name": "Sprint Qualifying",
        "session_type": "Qualifying",
        "year": 2023,
    }
    defaults.update(overrides)
    return Session(**defaults)


@pytest.mark.asyncio
async def test_list_sessions_forwards_filters_to_client() -> None:
    """Service forwards kwargs to the OpenF1 client unchanged."""
    client = MagicMock()
    expected = [_make_session(country_name="Belgium")]
    client.get = AsyncMock(return_value=expected)

    service = SessionService(client)
    result = await service.list_sessions(
        country_name="Belgium", session_name="Sprint Qualifying", year=2023
    )

    client.get.assert_called_once_with(
        "sessions",
        Session,
        country_name="Belgium",
        session_name="Sprint Qualifying",
        year=2023,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_list_sessions_forwards_latest_literal() -> None:
    """Service forwards session_key="latest" unchanged to the client."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = SessionService(client)
    await service.list_sessions(session_key="latest")

    client.get.assert_called_once_with("sessions", Session, session_key="latest")


@pytest.mark.asyncio
async def test_list_sessions_returns_empty_list() -> None:
    """Service returns an empty list when the client returns nothing."""
    client = MagicMock()
    client.get = AsyncMock(return_value=[])

    service = SessionService(client)
    result = await service.list_sessions()

    assert result == []
