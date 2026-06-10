"""Pydantic model for driver pace profile analysis."""

from typing import Literal

from pydantic import BaseModel, Field


class DriverPaceProfile(BaseModel):
    """Computed driver pace profile combining qualifying and race data."""

    driver_number: int = Field(description="Car number of the driver.")
    qpace_score: float = Field(
        description="Qualifying pace score (0–100), decay-weighted across recent sessions."
    )
    qpace_trend: Literal["IMPROVING", "DECLINING", "STABLE"] = Field(
        description="Trend direction comparing first-half vs second-half of sample sessions."
    )
    sector_1_delta: float | None = Field(
        default=None,
        description="Average delta to session-best in sector 1 across qualifying sessions (seconds).",
    )
    sector_2_delta: float | None = Field(
        default=None,
        description="Average delta to session-best in sector 2 across qualifying sessions (seconds).",
    )
    sector_3_delta: float | None = Field(
        default=None,
        description="Average delta to session-best in sector 3 across qualifying sessions (seconds).",
    )
    strongest_sector: Literal["S1", "S2", "S3"] | None = Field(
        default=None,
        description="Sector where the driver loses the least time vs field minimum.",
    )
    rpace_score: float | None = Field(
        default=None,
        description=(
            "Median normalised race lap duration (lap / session_median). "
            "Lower is faster. None if fewer than 3 clean laps."
        ),
    )
    rpace_percentile: float | None = Field(
        default=None,
        description="Percentile rank vs all drivers in the same sessions (0=slowest, 100=fastest).",
    )
    overtake_adjustment: float = Field(
        description=(
            "Average net positions gained in races where the driver started P10+. "
            "0.0 if no such races."
        ),
    )
    sample_races: int = Field(description="Number of race weekends included in the analysis.")
