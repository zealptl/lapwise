"""Pydantic model for OpenF1 /laps responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Lap(BaseModel):
    """A single lap record as returned by OpenF1's /laps endpoint."""

    date_start: datetime | None = Field(
        default=None, description="UTC timestamp when the lap started."
    )
    driver_number: int = Field(description="Car number of the driver.")
    duration_sector_1: float | None = Field(
        default=None, description="Duration of sector 1 in seconds."
    )
    duration_sector_2: float | None = Field(
        default=None, description="Duration of sector 2 in seconds."
    )
    duration_sector_3: float | None = Field(
        default=None, description="Duration of sector 3 in seconds."
    )
    i1_speed: int | None = Field(
        default=None, description="Speed trap reading at intermediate point 1 (km/h)."
    )
    i2_speed: int | None = Field(
        default=None, description="Speed trap reading at intermediate point 2 (km/h)."
    )
    is_pit_out_lap: bool | None = Field(
        default=None, description="Whether this lap started from the pit lane."
    )
    lap_duration: float | None = Field(default=None, description="Total lap time in seconds.")
    lap_number: int = Field(description="Lap number within the session.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    segments_sector_1: list[int] | None = Field(
        default=None,
        description="Mini-sector colour codes for sector 1 (0=unknown, 2048=yellow, 2049=green).",
    )
    segments_sector_2: list[int] | None = Field(
        default=None, description="Mini-sector colour codes for sector 2."
    )
    segments_sector_3: list[int] | None = Field(
        default=None, description="Mini-sector colour codes for sector 3."
    )
    session_key: int = Field(description="Unique identifier for the session.")
    st_speed: int | None = Field(
        default=None, description="Speed trap reading at the speed trap (km/h)."
    )
