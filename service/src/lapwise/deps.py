"""FastAPI dependency providers for Lapwise.

Each provider is injected by FastAPI's dependency injection system,
keeping route handlers free from direct instantiation of collaborators.
"""

from typing import Annotated

from fastapi import Depends, Request

from lapwise.clients.openf1 import OpenF1Client
from lapwise.services.drivers import DriverService
from lapwise.services.laps import LapService
from lapwise.services.meetings import MeetingService
from lapwise.services.overtakes import OvertakeService
from lapwise.services.pit import PitService
from lapwise.services.position import PositionService
from lapwise.services.session_result import SessionResultService
from lapwise.services.sessions import SessionService
from lapwise.services.stints import StintService


def get_openf1_client(request: Request) -> OpenF1Client:
    """Return the shared OpenF1Client stored on app state during lifespan startup."""
    client: OpenF1Client = request.app.state.openf1_client
    return client


async def get_auth() -> None:
    """No-op authentication dependency.

    This slot exists so an auth mechanism can be swapped in later
    without changing route signatures.  It currently accepts all requests.
    """
    return None


# ---------------------------------------------------------------------------
# Service providers
# ---------------------------------------------------------------------------


def get_session_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> SessionService:
    """Return a SessionService for the current request."""
    return SessionService(client)


def get_driver_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> DriverService:
    """Return a DriverService for the current request."""
    return DriverService(client)


def get_lap_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> LapService:
    """Return a LapService for the current request."""
    return LapService(client)


def get_overtake_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> OvertakeService:
    """Return an OvertakeService for the current request."""
    return OvertakeService(client)


def get_pit_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> PitService:
    """Return a PitService for the current request."""
    return PitService(client)


def get_session_result_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> SessionResultService:
    """Return a SessionResultService for the current request."""
    return SessionResultService(client)


def get_meeting_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> MeetingService:
    """Return a MeetingService for the current request."""
    return MeetingService(client)


def get_position_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> PositionService:
    """Return a PositionService wired to the shared OpenF1Client."""
    return PositionService(client)


def get_stint_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> StintService:
    """Return a StintService for the current request."""
    return StintService(client)
