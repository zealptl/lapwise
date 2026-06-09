"""Service layer for the OpenF1 /drivers endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.drivers import Driver


class DriverService:
    """Thin orchestrator that delegates to OpenF1Client for driver data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_drivers(self, **filters: Any) -> list[Driver]:
        """Return drivers matching filters.

        Args:
            **filters: Arbitrary keyword filters forwarded to OpenF1Client.

        Returns:
            A list of Driver instances.
        """
        return await self._client.get("drivers", Driver, **filters)
