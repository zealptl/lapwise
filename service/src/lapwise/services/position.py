"""Service layer for the OpenF1 /position endpoint."""

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.position import Position


class PositionService:
    """Wraps the OpenF1 /position endpoint with typed filter support."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def list_positions(
        self,
        *,
        session_key: int | None = None,
        meeting_key: int | None = None,
        driver_number: list[int] | None = None,
        position: int | None = None,
        position_lt: int | None = None,
        position_lte: int | None = None,
        position_gt: int | None = None,
        position_gte: int | None = None,
    ) -> list[Position]:
        """Fetch position records from OpenF1, applying optional filters.

        Comparison suffixes (_lt, _lte, _gt, _gte) are translated to
        OpenF1's native operator syntax (e.g. ``position_lte=3`` ->
        ``position<=3``) by the client's filter layer.
        """
        return await self._client.get(
            "position",
            Position,
            session_key=session_key,
            meeting_key=meeting_key,
            driver_number=driver_number,
            position=position,
            position_lt=position_lt,
            position_lte=position_lte,
            position_gt=position_gt,
            position_gte=position_gte,
        )
