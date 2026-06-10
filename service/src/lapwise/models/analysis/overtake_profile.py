"""Pydantic models for driver overtake profile analysis."""

from pydantic import BaseModel, Field


class OvertakeProfile(BaseModel):
    """Overtaking statistics and aggression metrics for a driver."""

    driver_number: int = Field(description="Official driver racing number.")
    overtakes_made: int = Field(description="Total positions gained via on-track overtakes.")
    overtakes_lost: int = Field(description="Total positions lost to on-track overtakes.")
    net_overtakes: int = Field(
        description="Net positions gained (overtakes_made minus overtakes_lost)."
    )
    overtake_rate: float = Field(
        description="Avg overtakes made per race session in sample."
    )
    defensive_rate: float = Field(
        description="Avg overtakes lost per race session in sample."
    )
    aggression_score: float = Field(
        description="Percentile rank of overtaking activity vs full field (0–100)."
    )
    circuit_overtake_avg: float | None = Field(
        default=None,
        description="Avg overtakes per race at the filtered circuit (populated when circuit filter is active).",
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
    total_races: int = Field(
        description="Total race and sprint sessions counted in the denominator."
    )
