"""Pydantic models for championship context analysis."""

from pydantic import BaseModel, Field


class DriverChampionshipContext(BaseModel):
    """Championship standings and momentum context for a single driver."""

    driver_number: int = Field(description="Official driver racing number.")
    full_name: str | None = Field(default=None, description="Driver's full name.")
    team_name: str | None = Field(default=None, description="Constructor name the driver races for.")
    points_current: float = Field(description="Driver's total championship points to date.")
    championship_position: int = Field(description="Driver's current championship standing position.")
    points_gap_to_leader: float = Field(
        description="Points deficit to the championship leader (0 if leader)."
    )
    points_gap_to_p3: float = Field(
        description="Points deficit to third place (negative if driver is above P3)."
    )
    momentum: str = Field(
        description="Recent scoring momentum vs season avg: POSITIVE, NEUTRAL, or NEGATIVE."
    )
    desperation_index: float = Field(
        description="Index representing urgency to score based on points gap vs remaining races (0–100)."
    )
    constructor_battle: bool = Field(
        description="Whether the driver's constructor is within 30 pts of an adjacent position."
    )


class ConstructorChampionshipContext(BaseModel):
    """Championship standings context for a constructor."""

    team_name: str = Field(description="Constructor name.")
    points_current: float = Field(description="Constructor's total championship points to date.")
    constructor_position: int = Field(description="Constructor's current championship standing position.")
    points_gap_to_leader: float = Field(
        description="Points gap to the leading constructor (0 for the leader)."
    )
    under_pressure: bool = Field(
        description="Whether the constructor is within 30 pts of an adjacent position."
    )


class ChampionshipContext(BaseModel):
    """Full championship context snapshot for a given season and round."""

    season: int = Field(description="Championship season year.")
    drivers: list[DriverChampionshipContext] = Field(
        description="Championship context for all drivers, ordered by position."
    )
    constructors: list[ConstructorChampionshipContext] = Field(
        description="Championship context for all constructors, ordered by position."
    )
