"""Service layer for the OpenF1 /stints endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.stints import Stint


class StintService:
    """Thin orchestrator that delegates to OpenF1Client for stint data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_stints(self, **filters: Any) -> list[Stint]:
        """Return stints matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes for tyre_age_at_start.

        Returns:
            A list of Stint instances.
        """
        return await self._client.get("stints", Stint, **filters)
