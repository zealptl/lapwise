"""Service layer for the OpenF1 /session_result endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.session_result import SessionResult


class SessionResultService:
    """Thin orchestrator that delegates to OpenF1Client for session result data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_results(self, **filters: Any) -> list[SessionResult]:
        """Return session results matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes (_lt, _lte, _gt, _gte) for position.

        Returns:
            A list of SessionResult instances.
        """
        return await self._client.get("session_result", SessionResult, **filters)
