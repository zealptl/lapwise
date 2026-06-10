"""Pydantic models for driver qualifying trend analysis."""

from pydantic import BaseModel, Field


class SectorStats(BaseModel):
    """Qualifying statistics for a single track sector."""

    avg_delta_to_fastest: float | None = Field(
        default=None, description="Avg gap to fastest sector time in field (seconds)."
    )
    dominance_rate: float = Field(
        description="Proportion of sessions where driver set fastest sector time."
    )


class SectorDominance(BaseModel):
    """Sector dominance breakdown across all three track sectors."""

    sector_1: SectorStats = Field(description="Dominance statistics for sector 1.")
    sector_2: SectorStats = Field(description="Dominance statistics for sector 2.")
    sector_3: SectorStats = Field(description="Dominance statistics for sector 3.")


class QualifyingTrends(BaseModel):
    """Qualifying performance trends for a driver over recent race weekends."""

    driver_number: int = Field(description="Official driver racing number.")
    avg_grid_position: float = Field(
        description="Average starting grid position in sample."
    )
    best_grid_position: int = Field(description="Best (lowest) grid position achieved in sample.")
    worst_grid_position: int = Field(
        description="Worst (highest) grid position achieved in sample."
    )
    q2_appearance_rate: float = Field(
        description="Proportion of qualifying sessions where driver reached Q2."
    )
    q3_appearance_rate: float = Field(
        description="Proportion of qualifying sessions where driver reached Q3."
    )
    sector_dominance: SectorDominance = Field(
        description="Sector dominance statistics broken down by sector."
    )
    strongest_sector: str | None = Field(
        default=None, description="Sector with smallest avg delta to fastest: S1, S2, or S3."
    )
    grid_vs_expected: float = Field(
        description="Delta between actual avg grid position and championship-position-expected position."
    )
    recent_trend: str = Field(
        description="Qualifying trend direction: IMPROVING, STABLE, or DECLINING."
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
