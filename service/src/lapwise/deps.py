"""FastAPI dependency providers for Lapwise.

Each provider is injected by FastAPI's dependency injection system,
keeping route handlers free from direct instantiation of collaborators.
"""

from typing import Annotated

from fastapi import Depends

from lapwise.clients.openf1 import OpenF1Client
from lapwise.config import get_settings
from lapwise.services.championship import ChampionshipDriverService, ChampionshipTeamService
from lapwise.services.drivers import DriverService
from lapwise.services.laps import LapService
from lapwise.services.meetings import MeetingService
from lapwise.services.overtakes import OvertakeService
from lapwise.services.pit import PitService
from lapwise.services.position import PositionService
from lapwise.services.session_result import SessionResultService
from lapwise.services.sessions import SessionService
from lapwise.services.starting_grid import StartingGridService
from lapwise.services.stints import StintService
from lapwise.services.weather import WeatherService


def get_openf1_client() -> OpenF1Client:
    """Create an OpenF1Client for this request."""
    return OpenF1Client(get_settings())


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


def get_starting_grid_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> StartingGridService:
    """Return a StartingGridService for the current request."""
    return StartingGridService(client)


def get_weather_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> WeatherService:
    """Return a WeatherService for the current request."""
    return WeatherService(client)


def get_championship_driver_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> ChampionshipDriverService:
    """Return a ChampionshipDriverService for the current request."""
    return ChampionshipDriverService(client)


def get_championship_team_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> ChampionshipTeamService:
    """Return a ChampionshipTeamService for the current request."""
    return ChampionshipTeamService(client)


def get_analysis_service(
    client: Annotated[OpenF1Client, Depends(get_openf1_client)],
) -> "AnalysisService":
    """Return an AnalysisService for the current request."""
    from lapwise.services.analysis import AnalysisService

    return AnalysisService(client)
