"""Pydantic models for F1 Fantasy price list."""

from pydantic import BaseModel, Field


class DriverPrice(BaseModel):
    """A single driver's F1 Fantasy price entry."""

    driver_number: int = Field(description="Official car/driver number.")
    full_name: str = Field(description="Driver's full name.")
    team_name: str = Field(description="Constructor/team name.")
    price_millions: float = Field(description="Fantasy price in millions (e.g. 30.0 = $30M).")


class ConstructorPrice(BaseModel):
    """A single constructor's F1 Fantasy price entry."""

    team_name: str = Field(description="Constructor/team name.")
    price_millions: float = Field(description="Fantasy price in millions (e.g. 33.5 = $33.5M).")


class FantasyPrices(BaseModel):
    """Full F1 Fantasy price list for a given season."""

    season: int = Field(description="F1 season year.")
    last_updated: str = Field(description="ISO 8601 date when prices were last updated (YYYY-MM-DD).")
    drivers: list[DriverPrice] = Field(description="All driver price entries for the season.")
    constructors: list[ConstructorPrice] = Field(description="All constructor price entries for the season.")
