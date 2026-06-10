"""Pydantic models for the DNF rates analysis endpoint."""

from pydantic import BaseModel, Field


class DnfBreakdown(BaseModel):
    """DNF/DNS/DSQ rate breakdown by session type."""

    qualifying_dnf_rate: float = Field(
        description="Fraction of qualifying sessions with a DNF/DNS/DSQ (0.0–1.0)."
    )
    race_dnf_rate: float = Field(
        description="Fraction of race sessions with a DNF/DNS/DSQ (0.0–1.0)."
    )
    sprint_dnf_rate: float = Field(
        description="Fraction of sprint sessions with a DNF/DNS/DSQ (0.0–1.0)."
    )


class DnfRates(BaseModel):
    """Aggregated DNF/DNS/DSQ statistics for a single driver."""

    driver_number: int = Field(description="Car number of the driver.")
    dnf_count: int = Field(description="Number of sessions where the driver DNF'd.")
    dns_count: int = Field(description="Number of sessions where the driver DNS'd.")
    dsq_count: int = Field(description="Number of sessions where the driver was DSQ'd.")
    total_sessions: int = Field(
        description="Number of sessions in which the driver has a result entry."
    )
    dnf_rate: float = Field(
        description="Combined (DNF + DNS + DSQ) / total_sessions rate (0.0–1.0)."
    )
    reliability_score: float = Field(
        description="Reliability expressed as a percentage: (1 - dnf_rate) * 100."
    )
    sample_races: int = Field(description="Number of race weekends included in the sample.")
    breakdown: DnfBreakdown = Field(description="Per-session-type DNF rate breakdown.")
