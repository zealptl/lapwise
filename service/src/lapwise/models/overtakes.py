"""Pydantic model for OpenF1 /overtakes responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Overtake(BaseModel):
    """An overtake event as returned by OpenF1's /overtakes endpoint.

    Note: data is only available during race sessions and may be incomplete.
    """

    date: datetime = Field(description="UTC timestamp when the overtake occurred.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    overtaken_driver_number: int = Field(description="Car number of the driver who was overtaken.")
    overtaking_driver_number: int = Field(
        description="Car number of the driver who made the overtake."
    )
    position: int = Field(description="Track position at which the overtake occurred.")
    session_key: int = Field(description="Unique identifier for the session.")
