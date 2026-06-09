"""Pydantic model for OpenF1 /meetings responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Meeting(BaseModel):
    """A Formula 1 race weekend (meeting) as returned by OpenF1's /meetings endpoint."""

    circuit_key: int = Field(description="Unique identifier for the circuit.")
    circuit_info_url: str | None = Field(
        default=None, description="URL for circuit information page."
    )
    circuit_image: str | None = Field(default=None, description="URL of the circuit layout image.")
    circuit_short_name: str | None = Field(
        default=None, description="Short display name of the circuit (e.g. Monza)."
    )
    circuit_type: str | None = Field(
        default=None,
        description="Circuit classification (e.g. permanent, street circuit).",
    )
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-3 country code (e.g. ITA)."
    )
    country_flag: str | None = Field(default=None, description="URL of the country flag image.")
    country_key: int | None = Field(
        default=None, description="OpenF1 internal identifier for the country."
    )
    country_name: str | None = Field(default=None, description="Full country name (e.g. Italy).")
    date_end: datetime | None = Field(
        default=None, description="UTC timestamp when the meeting ended."
    )
    date_start: datetime | None = Field(
        default=None, description="UTC timestamp when the meeting started."
    )
    gmt_offset: str | None = Field(
        default=None,
        description="UTC offset at the circuit location, formatted as HH:MM:SS.",
    )
    is_cancelled: bool = Field(
        description="Whether the meeting was cancelled before it took place."
    )
    location: str | None = Field(default=None, description="City or venue name (e.g. Monza).")
    meeting_key: int = Field(description="Unique identifier for this meeting.")
    meeting_name: str | None = Field(
        default=None, description="Short meeting name (e.g. Italian Grand Prix)."
    )
    meeting_official_name: str | None = Field(
        default=None,
        description="Full official meeting name including title sponsor.",
    )
    year: int = Field(description="Championship year in which the meeting takes place.")
