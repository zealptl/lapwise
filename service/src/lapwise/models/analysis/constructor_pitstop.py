"""Pydantic models for constructor pitstop performance analysis."""

from pydantic import BaseModel, Field


class ConstructorPitstop(BaseModel):
    """Pitstop performance statistics for a constructor."""

    team_name: str = Field(description="Constructor name.")
    avg_stop_duration: float | None = Field(
        default=None, description="Average stationary stop duration in seconds (null excluded, >60s excluded)."
    )
    avg_lane_duration: float | None = Field(
        default=None, description="Average total pit lane duration in seconds."
    )
    fastest_stop_in_sample: float | None = Field(
        default=None, description="Fastest individual stop duration recorded in sample (seconds)."
    )
    fantasy_points_avg: float = Field(
        description="Average fantasy points earned per stop based on duration brackets."
    )
    fastest_pitstop_rate: float = Field(
        description="Proportion of sessions where constructor set the fastest pitstop."
    )
    sub_2s_rate: float = Field(
        description="Proportion of stops completed in under 2.0 seconds."
    )
    consistency_score: float = Field(
        description="Consistency metric derived from std deviation of stop durations (higher is more consistent)."
    )
    sample_stops: int = Field(description="Total number of valid pitstops included in the sample.")
    sample_races: int = Field(description="Number of race weekends included in the sample.")
