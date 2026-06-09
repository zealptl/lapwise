"""Pydantic models for OpenF1 /championship_drivers and /championship_teams responses."""

from pydantic import BaseModel, Field


class ChampionshipDriver(BaseModel):
    """A championship driver standing as returned by OpenF1's /championship_drivers endpoint.

    Note: this endpoint is marked beta by OpenF1 and only covers race sessions.
    """

    driver_number: int = Field(description="Car number of the driver.")
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    points_current: float = Field(description="Championship points after this meeting.")
    points_start: float = Field(description="Championship points before this meeting.")
    position_current: int = Field(description="Championship position after this meeting.")
    position_start: int = Field(description="Championship position before this meeting.")
    session_key: int = Field(description="Unique identifier for the session.")


class ChampionshipTeam(BaseModel):
    """A championship team standing as returned by OpenF1's /championship_teams endpoint.

    Note: this endpoint is marked beta by OpenF1 and only covers race sessions.
    """

    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    points_current: float = Field(description="Championship points after this meeting.")
    points_start: float = Field(description="Championship points before this meeting.")
    position_current: int = Field(description="Championship position after this meeting.")
    position_start: int = Field(description="Championship position before this meeting.")
    session_key: int = Field(description="Unique identifier for the session.")
    team_name: str = Field(description="Constructor/team name.")
