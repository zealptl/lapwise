"""Service layer for the OpenF1 /overtakes endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.overtakes import Overtake


class OvertakeService:
    """Thin orchestrator that delegates to OpenF1Client for overtake data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_overtakes(self, **filters: Any) -> list[Overtake]:
        """Return overtakes matching filters.

        Args:
            **filters: Arbitrary keyword filters forwarded to OpenF1Client.

        Returns:
            A list of Overtake instances.
        """
        return await self._client.get("overtakes", Overtake, **filters)
