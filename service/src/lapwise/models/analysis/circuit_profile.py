"""Pydantic models for circuit profile analysis."""

from pydantic import BaseModel, Field


class CircuitProfile(BaseModel):
    """Historical characteristic profile for an F1 circuit."""

    circuit_key: int = Field(description="OpenF1 unique identifier for the circuit.")
    circuit_short_name: str | None = Field(
        default=None, description="Short display name of the circuit (e.g. Monza)."
    )
    overtake_difficulty: str = Field(
        description="Overtaking difficulty classification: LOW, MEDIUM, or HIGH."
    )
    qualifying_importance: float = Field(
        description="Derived importance of qualifying position for race outcome (0–1)."
    )
    avg_overtakes_per_race: float = Field(
        description="Average number of on-track overtakes per race in sample."
    )
    safety_car_tendency: str = Field(
        description="Likelihood of safety car deployment: LOW, MEDIUM, or HIGH."
    )
    typical_compounds: list[str] = Field(
        description="Tyre compound names used most frequently at this circuit, ordered by frequency."
    )
    weather_variability: str = Field(
        description="Likelihood of mixed-weather conditions: LOW, MEDIUM, or HIGH."
    )
    fl_typical_lap: float | None = Field(
        default=None, description="Avg fastest race lap time at this circuit (seconds)."
    )
    avg_pit_stops: float = Field(
        description="Average number of pit stops per car per race in sample."
    )
    sample_years: int = Field(description="Number of seasons included in the sample.")
