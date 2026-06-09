"""Pydantic model for an OpenF1 session."""

from datetime import datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    """A single Formula 1 session as returned by OpenF1's /sessions endpoint."""

    circuit_key: int = Field(description="Unique identifier for the circuit.")
    circuit_short_name: str | None = Field(
        default=None, description="Short display name of the circuit (e.g. Spa)."
    )
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-3 country code (e.g. BEL)."
    )
    country_key: int | None = Field(
        default=None, description="OpenF1 internal identifier for the country."
    )
    country_name: str | None = Field(default=None, description="Full country name (e.g. Belgium).")
    date_end: datetime | None = Field(
        default=None, description="UTC timestamp when the session ended."
    )
    date_start: datetime | None = Field(
        default=None, description="UTC timestamp when the session started."
    )
    gmt_offset: str | None = Field(
        default=None,
        description="UTC offset at the circuit location, formatted as HH:MM:SS (e.g. 02:00:00).",
    )
    is_cancelled: bool = Field(
        description="Whether the session was cancelled before it took place."
    )
    location: str | None = Field(
        default=None, description="City or venue name of the circuit (e.g. Spa-Francorchamps)."
    )
    meeting_key: int = Field(description="Unique identifier for the parent meeting (race weekend).")
    session_key: int = Field(description="Unique identifier for this session.")
    session_name: str | None = Field(
        default=None,
        description="Human-readable session name (e.g. Race, Qualifying, Sprint Qualifying).",
    )
    session_type: str | None = Field(
        default=None,
        description="Category of session: Race, Qualifying, Practice, or Sprint.",
    )
    year: int = Field(description="Championship year in which the session took place.")
