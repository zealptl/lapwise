"""Pydantic model for OpenF1 /pit responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class PitStop(BaseModel):
    """A pit stop event as returned by OpenF1's /pit endpoint."""

    date: datetime = Field(description="UTC timestamp when the pit stop occurred.")
    driver_number: int = Field(description="Car number of the driver.")
    lane_duration: float | None = Field(
        default=None, description="Time spent in the pit lane (seconds)."
    )
    lap_number: int = Field(description="Lap on which the pit stop took place.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    pit_duration: float | None = Field(
        default=None,
        description="Deprecated alias for lane_duration; time spent in the pit lane (seconds).",
    )
    session_key: int = Field(description="Unique identifier for the session.")
    stop_duration: float | None = Field(
        default=None, description="Duration of the stationary stop itself (seconds)."
    )
