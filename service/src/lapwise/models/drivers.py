"""Pydantic model for OpenF1 /drivers responses."""

from pydantic import BaseModel, Field


class Driver(BaseModel):
    """A Formula 1 driver entry as returned by OpenF1's /drivers endpoint."""

    broadcast_name: str | None = Field(
        default=None,
        description="Name used in broadcast graphics (e.g. VER).",
    )
    country_code: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-3 country code of the driver's nationality (e.g. NED).",
    )
    driver_number: int = Field(description="Unique car number assigned to the driver.")
    first_name: str | None = Field(default=None, description="Driver's first name.")
    full_name: str | None = Field(
        default=None, description="Driver's full name (e.g. Max Verstappen)."
    )
    headshot_url: str | None = Field(
        default=None, description="URL of the driver's official headshot image."
    )
    last_name: str | None = Field(default=None, description="Driver's last name.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting (race weekend).")
    name_acronym: str | None = Field(
        default=None, description="Three-letter driver acronym used in timing displays (e.g. VER)."
    )
    session_key: int = Field(description="Unique identifier for the session.")
    team_colour: str | None = Field(
        default=None, description="Hex colour code for the driver's team (e.g. 3671C6)."
    )
    team_name: str | None = Field(
        default=None, description="Name of the constructor team (e.g. Red Bull Racing)."
    )
