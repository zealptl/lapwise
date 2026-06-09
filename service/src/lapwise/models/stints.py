"""Pydantic model for OpenF1 /stints responses."""

from pydantic import BaseModel, Field


class Stint(BaseModel):
    """A tyre stint as returned by OpenF1's /stints endpoint."""

    compound: str | None = Field(
        default=None,
        description=(
            "Tyre compound used during the stint. "
            "Expected values: SOFT, MEDIUM, HARD, INTERMEDIATE, WET, UNKNOWN."
        ),
    )
    driver_number: int = Field(description="Car number of the driver.")
    lap_end: int | None = Field(default=None, description="Last lap number of the stint.")
    lap_start: int = Field(description="First lap number of the stint.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    session_key: int = Field(description="Unique identifier for the session.")
    stint_number: int = Field(description="Sequential stint number for this driver in the session.")
    tyre_age_at_start: int | None = Field(
        default=None,
        description="Age of the tyres at the start of the stint (in laps).",
    )
