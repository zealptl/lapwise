"""Pydantic model for OpenF1 /weather responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Weather(BaseModel):
    """A weather sample as returned by OpenF1's /weather endpoint."""

    air_temperature: float | None = Field(default=None, description="Ambient air temperature (°C).")
    date: datetime = Field(description="UTC timestamp of the sample.")
    humidity: float | None = Field(default=None, description="Relative humidity (%).")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    pressure: float | None = Field(default=None, description="Atmospheric pressure (mbar).")
    rainfall: int | None = Field(default=None, description="Rainfall indicator (0 = dry, 1 = wet).")
    session_key: int = Field(description="Unique identifier for the session.")
    track_temperature: float | None = Field(
        default=None, description="Track surface temperature (°C)."
    )
    wind_direction: int | None = Field(
        default=None, description="Wind direction in degrees (0-359)."
    )
    wind_speed: float | None = Field(default=None, description="Wind speed (m/s).")
