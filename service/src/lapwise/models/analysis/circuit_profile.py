"""Pydantic model for the Circuit Profile analysis endpoint."""

from pydantic import BaseModel, Field


class CircuitProfile(BaseModel):
    """Derived circuit characteristics computed from historical race data."""

    circuit_key: int = Field(description="OpenF1 circuit identifier.")
    circuit_short_name: str | None = Field(
        default=None, description="Short display name of the circuit (e.g. Monaco)."
    )
    sample_years: int = Field(description="Number of years included in the analysis window.")
    race_sessions_found: int = Field(
        description="Number of race sessions found within the sample window."
    )

    # Derived fields — null/0 when fewer than 2 race sessions are available
    overtake_difficulty: str | None = Field(
        default=None,
        description=(
            "Difficulty of overtaking at this circuit: HIGH (<15 avg overtakes/race), "
            "MEDIUM (15–30), or LOW (>30)."
        ),
    )
    avg_overtakes_per_race: float | None = Field(
        default=None,
        description="Mean number of overtakes per race session in the sample window.",
    )
    qualifying_importance: int | None = Field(
        default=None,
        description=(
            "Estimated importance of qualifying position on race outcome (0–100). "
            "Derived from overtake_difficulty: HIGH→100, MEDIUM→67, LOW→33."
        ),
    )
    safety_car_tendency: str | None = Field(
        default=None,
        description=(
            "Tendency for safety car periods: HIGH (>15% of laps above 110% of session median), "
            "MEDIUM (5–15%), or LOW (<5%)."
        ),
    )
    weather_variability: str | None = Field(
        default=None,
        description=(
            "Variability of weather conditions: HIGH (>30% of weather records show rainfall), "
            "MEDIUM (10–30%), or LOW (<10%)."
        ),
    )
    typical_compounds: list[str] = Field(
        default_factory=list,
        description="Tyre compounds used at this circuit, ordered by frequency (most common first).",
    )
    fl_typical_lap: float | None = Field(
        default=None,
        description=(
            "Average lap number on which the fastest lap is set, "
            "excluding safety-car-influenced laps."
        ),
    )
    avg_pit_stops: float = Field(
        default=0.0,
        description="Average number of pit stops per driver per race.",
    )
