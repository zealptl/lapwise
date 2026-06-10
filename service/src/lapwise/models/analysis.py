"""Pydantic response models for the /v1/analysis endpoints."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1.1 Driver Pace Profile
# ---------------------------------------------------------------------------


class CircuitYearData(BaseModel):
    """Historical lap and stint data for a single past year."""

    year: int = Field(description="Championship year.")
    avg_lap_time_ms: float | None = Field(
        default=None, description="Average race lap time in milliseconds for this year."
    )
    avg_stint_length: float | None = Field(
        default=None, description="Average stint length in laps for this year."
    )


class DriverPaceProfile(BaseModel):
    """Aggregated pace profile for a driver at a specific circuit and year."""

    driver_number: int = Field(description="Car number of the driver.")
    circuit_key: int = Field(description="OpenF1 circuit identifier.")
    year: int = Field(description="Championship year.")
    avg_lap_time_ms: float | None = Field(
        default=None, description="Average race lap time in milliseconds for the requested year."
    )
    avg_stint_length: float | None = Field(
        default=None,
        description="Average stint length in laps across all stints for the requested year.",
    )
    circuit_history: list[CircuitYearData] = Field(
        default_factory=list,
        description="Historical data for year-1 and year-2 when include_circuit_history=True.",
    )


# ---------------------------------------------------------------------------
# 1.3 DNF Rates
# ---------------------------------------------------------------------------


class DriverDnfStats(BaseModel):
    """Per-driver DNF statistics."""

    driver_number: int = Field(description="Car number of the driver.")
    dnf_count: int = Field(description="Number of DNFs at this circuit over the sample period.")
    total_races: int = Field(description="Total races included in the sample.")
    dnf_rate_pct: float = Field(description="DNF rate as a percentage (0-100).")


class ConstructorDnfStats(BaseModel):
    """Per-constructor aggregated DNF statistics."""

    team_name: str = Field(description="Constructor/team name.")
    dnf_count: int = Field(description="Total DNFs across all drivers for this constructor.")
    total_entries: int = Field(description="Total driver-race entries for this constructor.")
    dnf_rate_pct: float = Field(description="DNF rate as a percentage (0-100).")


class DnfRates(BaseModel):
    """DNF rates for a circuit over a sample window."""

    circuit_key: int = Field(description="OpenF1 circuit identifier.")
    year: int = Field(description="Reference championship year.")
    last_n_races: int = Field(description="Number of most-recent races used in the sample.")
    driver_dnf_stats: list[DriverDnfStats] = Field(
        default_factory=list, description="Per-driver DNF statistics."
    )
    constructor_dnf_stats: list[ConstructorDnfStats] = Field(
        default_factory=list, description="Per-constructor DNF statistics."
    )


# ---------------------------------------------------------------------------
# 1.4 Fastest Lap Candidates
# ---------------------------------------------------------------------------


class FastestLapCandidate(BaseModel):
    """A driver's fastest-lap count at a circuit across historical sessions."""

    driver_number: int = Field(description="Car number of the driver.")
    fastest_lap_count: int = Field(
        description="Number of sessions where this driver recorded the fastest lap."
    )
    frequency_pct: float = Field(
        description="Percentage of sessions where this driver had the fastest lap (0-100)."
    )


# ---------------------------------------------------------------------------
# 1.5 Overtake Profile
# ---------------------------------------------------------------------------


class OvertakeProfile(BaseModel):
    """Overtake statistics for a driver at a circuit."""

    driver_number: int = Field(description="Car number of the driver.")
    overtakes_made: int = Field(description="Total overtakes made by this driver.")
    positions_gained_avg: float = Field(
        description=(
            "Average net positions gained from starting grid to final race result "
            "(positive = moved forward)."
        )
    )


# ---------------------------------------------------------------------------
# 1.6 Circuit Profile
# ---------------------------------------------------------------------------


class CircuitProfile(BaseModel):
    """Aggregated circuit characteristics derived from historical session data."""

    circuit_key: int = Field(description="OpenF1 circuit identifier.")
    year: int = Field(description="Reference championship year.")
    overtake_difficulty: str = Field(
        description="Qualitative overtaking difficulty: 'low', 'medium', or 'high'."
    )
    pitstop_frequency_avg: float = Field(
        description="Average number of pit stops per driver per race."
    )
    tyre_strategies: list[str] = Field(
        description="Distinct tyre compounds observed in race sessions."
    )
    safety_car_probability_pct: float = Field(
        description=(
            "Estimated probability of a safety car appearance, expressed as a percentage (0-100). "
            "Derived from the share of laps in a session where rainfall was detected."
        )
    )


# ---------------------------------------------------------------------------
# 1.7 Championship Context
# ---------------------------------------------------------------------------


class DriverStanding(BaseModel):
    """A single driver's championship standing."""

    driver_number: int = Field(description="Car number of the driver.")
    position: int = Field(description="Current championship position.")
    points: float = Field(description="Current championship points tally.")
    team_name: str | None = Field(default=None, description="Constructor/team name.")


class TeamStanding(BaseModel):
    """A single constructor's championship standing."""

    team_name: str = Field(description="Constructor/team name.")
    position: int = Field(description="Current constructors' championship position.")
    points: float = Field(description="Current championship points tally.")


class ChampionshipContext(BaseModel):
    """Current driver and constructor championship standings."""

    year: int = Field(description="Championship year.")
    driver_standings: list[DriverStanding] = Field(
        default_factory=list, description="Driver standings ordered by position."
    )
    team_standings: list[TeamStanding] = Field(
        default_factory=list, description="Constructor standings ordered by position."
    )


# ---------------------------------------------------------------------------
# 1.8 Qualifying Trends
# ---------------------------------------------------------------------------


class QualifyingTrend(BaseModel):
    """A driver's qualifying performance trend at a circuit."""

    driver_number: int = Field(description="Car number of the driver.")
    avg_qualifying_position: float = Field(
        description="Average starting grid position across historical sessions at this circuit."
    )
    q3_appearances: int = Field(
        description="Number of times the driver qualified in the top 10 (grid position 1-10)."
    )
    q3_frequency_pct: float = Field(
        description=(
            "Percentage of sessions where the driver qualified in the top 10 (0-100). "
            "Used as a proxy for Q3 appearances."
        )
    )


# ---------------------------------------------------------------------------
# 1.9 Constructor Pit Stop Performance
# ---------------------------------------------------------------------------


class ConstructorPitstop(BaseModel):
    """Aggregated pit stop performance for a constructor at a circuit."""

    team_name: str = Field(description="Constructor/team name.")
    avg_pit_duration_ms: float = Field(
        description="Average stationary stop duration in milliseconds."
    )
    pit_count_avg: float = Field(description="Average number of pit stops per race entry.")
    under_2s_frequency_pct: float = Field(
        description="Percentage of stops completed in under 2 seconds (0-100)."
    )
    under_3s_frequency_pct: float = Field(
        description="Percentage of stops completed in under 3 seconds (0-100)."
    )
