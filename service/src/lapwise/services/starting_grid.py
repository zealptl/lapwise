"""Service layer for the OpenF1 /starting_grid endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.starting_grid import StartingGridEntry


class StartingGridService:
    """Thin orchestrator that delegates to OpenF1Client for starting grid data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_grid(self, **filters: Any) -> list[StartingGridEntry]:
        """Return starting grid entries matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes for position.

        Returns:
            A list of StartingGridEntry instances.
        """
        return await self._client.get("starting_grid", StartingGridEntry, **filters)
