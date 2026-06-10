"""Pydantic models for driver pace profile analysis."""

from pydantic import BaseModel, Field


class SectorDominance(BaseModel):
    """Sector-level dominance statistics for a driver."""

    avg_delta_to_fastest: float | None = Field(
        default=None, description="Avg gap to fastest sector time in field (seconds)."
    )
    dominance_rate: float = Field(
        description="Proportion of sessions where driver set fastest sector time."
    )


class DriverPaceProfile(BaseModel):
    """Pace profile for a driver across qualifying and race sessions."""

    driver_number: int = Field(description="Official driver racing number.")
    qpace_score: float = Field(
        description="Decay-weighted qualifying pace score relative to field."
    )
    qpace_trend: str = Field(
        description="Qualifying pace trend direction: IMPROVING, STABLE, or DECLINING."
    )
    sector_1_delta: float | None = Field(
        default=None, description="Avg delta to fastest S1 time in qualifying (seconds)."
    )
    sector_2_delta: float | None = Field(
        default=None, description="Avg delta to fastest S2 time in qualifying (seconds)."
    )
    sector_3_delta: float | None = Field(
        default=None, description="Avg delta to fastest S3 time in qualifying (seconds)."
    )
    strongest_sector: str | None = Field(
        default=None, description="Sector with smallest avg delta: S1, S2, or S3."
    )
    rpace_score: float | None = Field(
        default=None, description="Clean-air race pace score relative to field."
    )
    rpace_percentile: float | None = Field(
        default=None, description="Percentile rank of race pace score vs full field (0–100)."
    )
    overtake_adjustment: float = Field(
        description="Pace score adjustment applied for races started from P10 or lower."
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
