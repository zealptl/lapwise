"""Service layer for the OpenF1 /pit endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.pit import PitStop


class PitService:
    """Thin orchestrator that delegates to OpenF1Client for pit stop data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_pit_stops(self, **filters: Any) -> list[PitStop]:
        """Return pit stops matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes (_lt, _lte, _gt, _gte) for stop_duration.

        Returns:
            A list of PitStop instances.
        """
        return await self._client.get("pit", PitStop, **filters)
