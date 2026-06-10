"""Pydantic response model for the fastest lap candidates analysis endpoint."""

from pydantic import BaseModel, Field


class FastestLapCandidate(BaseModel):
    """Per-driver fastest lap probability metrics derived from historical Race and Sprint sessions."""

    driver_number: int = Field(description="Car number of the driver.")
    fastest_lap_count: int = Field(
        description="Number of sessions where this driver set the fastest eligible lap."
    )
    total_sessions: int = Field(
        description="Total number of Race and Sprint sessions in the sample."
    )
    fl_rate: float = Field(
        description="Fastest lap rate: fastest_lap_count / total_sessions (0.0–1.0)."
    )
    typical_fl_position: float | None = Field(
        default=None,
        description=(
            "Average finishing position (from session_result.position) in sessions "
            "where this driver set the fastest lap. Null if no FL recorded."
        ),
    )
    fl_on_fresh_tyre_rate: float | None = Field(
        default=None,
        description=(
            "Proportion of FL sessions where the fastest lap was set on a fresh tyre "
            "(tyre_age <= 2). Null if no FL recorded."
        ),
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
