"""Pydantic response models for the Qualifying Trends analysis endpoint."""

from pydantic import BaseModel, Field


class SectorStats(BaseModel):
    """Statistics for a single sector across qualifying sessions."""

    avg_delta_to_fastest: float | None = Field(
        default=None,
        description="Average gap (seconds) to the field's best sector time across sessions.",
    )
    dominance_rate: float | None = Field(
        default=None,
        description=(
            "Fraction of qualifying sessions in which this driver set "
            "the overall fastest sector time (0.0–1.0)."
        ),
    )


class SectorDominance(BaseModel):
    """Per-sector dominance breakdown across qualifying sessions."""

    sector_1: SectorStats = Field(description="Sector 1 statistics.")
    sector_2: SectorStats = Field(description="Sector 2 statistics.")
    sector_3: SectorStats = Field(description="Sector 3 statistics.")


class QualifyingTrends(BaseModel):
    """Aggregated qualifying performance trends for a single driver."""

    driver_number: int = Field(description="Car number of the driver.")
    sessions_analysed: int = Field(
        description="Number of qualifying sessions included in the analysis."
    )
    avg_grid_position: float | None = Field(
        default=None,
        description="Decay-weighted average grid position (decay factor 0.85, most-recent = weight 1).",
    )
    best_grid_position: int | None = Field(
        default=None,
        description="Best (lowest) grid position achieved across the sampled sessions.",
    )
    worst_grid_position: int | None = Field(
        default=None,
        description="Worst (highest number) grid position achieved across the sampled sessions.",
    )
    q3_appearance_rate: float | None = Field(
        default=None,
        description="Fraction of sessions where the driver started from positions 1–10 (Q3 proxy).",
    )
    q2_appearance_rate: float | None = Field(
        default=None,
        description="Fraction of sessions where the driver started from positions 1–15 (Q2 proxy).",
    )
    sector_dominance: SectorDominance = Field(
        description="Per-sector dominance statistics derived from qualifying lap data."
    )
    strongest_sector: int | None = Field(
        default=None,
        description=(
            "Sector number (1, 2, or 3) where the driver has the smallest average gap "
            "to the field fastest. None if no sector data is available."
        ),
    )
    grid_vs_expected: float | None = Field(
        default=None,
        description=(
            "Average difference between actual grid position and championship position "
            "at the time of the race. Negative means qualifying ahead of championship standing."
        ),
    )
    recent_trend: str | None = Field(
        default=None,
        description=(
            "Direction of grid position trend: IMPROVING, STABLE, or DECLINING. "
            "Computed by comparing the decay-weighted average of the older half of sessions "
            "against the newer half (threshold ±10%)."
        ),
    )
