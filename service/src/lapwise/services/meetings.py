"""Service layer for the OpenF1 /meetings endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.meetings import Meeting


class MeetingService:
    """Thin orchestrator that delegates to OpenF1Client for meeting data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_meetings(self, **filters: Any) -> list[Meeting]:
        """Return meetings matching filters.

        Args:
            **filters: Arbitrary keyword filters forwarded to OpenF1Client.

        Returns:
            A list of Meeting instances.
        """
        return await self._client.get("meetings", Meeting, **filters)
