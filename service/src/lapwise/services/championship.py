"""Service layer for OpenF1 /championship_drivers and /championship_teams endpoints."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.championship import ChampionshipDriver, ChampionshipTeam


class ChampionshipDriverService:
    """Thin orchestrator for championship driver standings."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_standings(self, **filters: Any) -> list[ChampionshipDriver]:
        """Return championship driver standings matching filters."""
        return await self._client.get("championship_drivers", ChampionshipDriver, **filters)


class ChampionshipTeamService:
    """Thin orchestrator for championship team standings."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_standings(self, **filters: Any) -> list[ChampionshipTeam]:
        """Return championship team standings matching filters."""
        return await self._client.get("championship_teams", ChampionshipTeam, **filters)
