"""Service layer for the OpenF1 /laps endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.laps import Lap


class LapService:
    """Thin orchestrator that delegates to OpenF1Client for lap data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_laps(self, **filters: Any) -> list[Lap]:
        """Return laps matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes (_lt, _lte, _gt, _gte).

        Returns:
            A list of Lap instances.
        """
        return await self._client.get("laps", Lap, **filters)
