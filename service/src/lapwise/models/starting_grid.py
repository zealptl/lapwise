"""Pydantic model for OpenF1 /starting_grid responses."""

from pydantic import BaseModel, Field


class StartingGridEntry(BaseModel):
    """A starting grid entry as returned by OpenF1's /starting_grid endpoint."""

    driver_number: int = Field(description="Car number of the driver.")
    lap_duration: float | None = Field(
        default=None, description="Qualifying lap time that set this grid position (seconds)."
    )
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    position: int = Field(description="Starting grid position (1 = pole position).")
    session_key: int = Field(description="Unique identifier for the session.")
