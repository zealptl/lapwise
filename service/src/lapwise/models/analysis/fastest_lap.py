"""Pydantic models for fastest lap candidate analysis."""

from pydantic import BaseModel, Field


class FastestLapCandidate(BaseModel):
    """Fastest lap statistics for a driver across race sessions."""

    driver_number: int = Field(description="Official driver racing number.")
    fastest_lap_count: int = Field(
        description="Number of sessions where driver set the fastest lap."
    )
    total_sessions: int = Field(
        description="Total race and sprint sessions in sample."
    )
    fl_rate: float = Field(
        description="Proportion of sessions where driver set the fastest lap."
    )
    typical_fl_position: float | None = Field(
        default=None, description="Avg finishing position in sessions where driver set fastest lap."
    )
    fl_on_fresh_tyre_rate: float | None = Field(
        default=None,
        description="Proportion of fastest laps set on fresh (low tyre_age) tyres.",
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
