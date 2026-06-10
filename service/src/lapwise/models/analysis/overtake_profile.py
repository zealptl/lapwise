"""Pydantic response model for the overtake profile analysis endpoint."""

from pydantic import BaseModel, Field


class OvertakeProfile(BaseModel):
    """Offensive and defensive overtake statistics for a single driver."""

    driver_number: int = Field(description="Car number of the driver.")
    overtakes_made: int = Field(description="Total overtakes made by this driver across the sample.")
    overtakes_lost: int = Field(
        description="Total times this driver was overtaken across the sample."
    )
    net_overtakes: int = Field(description="overtakes_made minus overtakes_lost.")
    overtake_rate: float = Field(
        description="Average overtakes made per session (overtakes_made / total_races)."
    )
    defensive_rate: float = Field(
        description="Average times overtaken per session (overtakes_lost / total_races)."
    )
    aggression_score: float = Field(
        description=(
            "Percentile rank of overtake_rate vs all drivers in the same sample, "
            "normalized 0–100 (100 = most overtakes made)."
        )
    )
    circuit_overtake_avg: float | None = Field(
        default=None,
        description=(
            "Average overtakes made per session at the specific circuit. "
            "Only populated when session_key or include_circuit_history is provided."
        ),
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
    total_races: int = Field(
        description=(
            "Total Race + Sprint sessions counted. "
            "Sprint weekends contribute 2 sessions to this denominator."
        )
    )
