"""Analysis response models."""

# Original consolidated models (used by analysis_service.py and routes/analysis/__init__.py)
from lapwise.models.analysis.analysis_models import (
    ChampionshipContext,
    CircuitProfile,
    CircuitYearData,
    ConstructorDnfStats,
    ConstructorPitstop,
    DriverDnfStats,
    DriverPaceProfile,
    DriverStanding,
    DnfRates,
    FastestLapCandidate,
    OvertakeProfile,
    QualifyingTrend,
    TeamStanding,
)

# Spec-aligned models (used by v1/analysis/* route modules)
from lapwise.models.analysis.championship_context import (
    ChampionshipContext as ChampionshipContextV2,
    ConstructorChampionshipContext,
    DriverChampionshipContext,
)
from lapwise.models.analysis.circuit_profile import CircuitProfile as CircuitProfileV2
from lapwise.models.analysis.constructor_pitstop import ConstructorPitstop as ConstructorPitstopV2
from lapwise.models.analysis.dnf_rates import DnfBreakdown, DnfRates as DnfRatesV2
from lapwise.models.analysis.driver_pace import DriverPaceProfile as DriverPaceProfileV2
from lapwise.models.analysis.fastest_lap import FastestLapCandidate as FastestLapCandidateV2
from lapwise.models.analysis.overtake_profile import OvertakeProfile as OvertakeProfileV2
from lapwise.models.analysis.qualifying_trends import QualifyingTrends

__all__ = [
    # Original models
    "ChampionshipContext",
    "CircuitProfile",
    "CircuitYearData",
    "ConstructorDnfStats",
    "ConstructorPitstop",
    "DriverDnfStats",
    "DriverPaceProfile",
    "DriverStanding",
    "DnfRates",
    "FastestLapCandidate",
    "OvertakeProfile",
    "QualifyingTrend",
    "TeamStanding",
    # Spec-aligned models
    "ChampionshipContextV2",
    "CircuitProfileV2",
    "ConstructorChampionshipContext",
    "ConstructorPitstopV2",
    "DnfBreakdown",
    "DnfRatesV2",
    "DriverChampionshipContext",
    "DriverPaceProfileV2",
    "FastestLapCandidateV2",
    "OvertakeProfileV2",
    "QualifyingTrends",
]
