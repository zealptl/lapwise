"""Service layer for the OpenF1 /weather endpoint."""

from typing import Any

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.weather import Weather


class WeatherService:
    """Thin orchestrator that delegates to OpenF1Client for weather data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_weather(self, **filters: Any) -> list[Weather]:
        """Return weather samples matching filters.

        Args:
            **filters: Keyword filters forwarded to OpenF1Client, including
                comparison suffixes for measurement fields.

        Returns:
            A list of Weather instances.
        """
        return await self._client.get("weather", Weather, **filters)
