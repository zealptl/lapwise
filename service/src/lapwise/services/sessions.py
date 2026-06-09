"""Service layer for the OpenF1 /sessions endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.sessions import Session


class SessionService:
    """Thin orchestrator that delegates to OpenF1Client for session data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_sessions(self, **filters: Any) -> list[Session]:
        """Return sessions matching filters.

        Parameters are forwarded verbatim to OpenF1Client.get; the
        client handles filter-syntax translation (equality, _lt/_lte/
        _gt/_gte suffixes, and the latest literal for session_key).

        Args:
            **filters: Arbitrary keyword filters (e.g. country_name,
                session_key, year).

        Returns:
            A list of Session instances.
        """
        return await self._client.get("sessions", Session, **filters)
