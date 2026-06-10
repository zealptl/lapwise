"""Pydantic models for driver DNF rate analysis."""

from pydantic import BaseModel, Field


class DnfBreakdown(BaseModel):
    """DNF rates broken down by session type."""

    qualifying_dnf_rate: float = Field(description="DNF rate across qualifying sessions.")
    race_dnf_rate: float = Field(description="DNF rate across race sessions.")
    sprint_dnf_rate: float = Field(description="DNF rate across sprint sessions.")


class DnfRates(BaseModel):
    """Reliability and DNF statistics for a driver."""

    driver_number: int = Field(description="Official driver racing number.")
    dnf_count: int = Field(description="Total number of did-not-finish results in sample.")
    dns_count: int = Field(description="Total number of did-not-start results in sample.")
    dsq_count: int = Field(description="Total number of disqualification results in sample.")
    total_sessions: int = Field(
        description="Total competitive sessions in sample (Qualifying, Race, Sprint)."
    )
    dnf_rate: float = Field(description="Overall DNF rate across all sessions in sample.")
    reliability_score: float = Field(
        description="Composite reliability score (higher is more reliable)."
    )
    breakdown: DnfBreakdown = Field(description="DNF rates broken down by session type.")
    sample_races: int = Field(description="Number of race weekends included in the sample.")
