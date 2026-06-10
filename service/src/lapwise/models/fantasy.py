"""Pydantic response models for the /v1/fantasy endpoints."""

from pydantic import BaseModel, Field


class DriverPrice(BaseModel):
    """F1 Fantasy price entry for a driver."""

    driver_number: int = Field(description="Car number of the driver.")
    full_name: str = Field(description="Driver's full name.")
    abbreviation: str = Field(description="Three-letter driver abbreviation.")
    team: str = Field(description="Constructor/team name.")
    price_millions: float = Field(description="Fantasy price in millions of dollars.")


class ConstructorPrice(BaseModel):
    """F1 Fantasy price entry for a constructor."""

    name: str = Field(description="Full constructor name.")
    abbreviation: str = Field(description="Short constructor abbreviation.")
    price_millions: float = Field(description="Fantasy price in millions of dollars.")


class FantasyPrices(BaseModel):
    """2025 F1 Fantasy prices for all drivers and constructors."""

    drivers: list[DriverPrice] = Field(description="Driver price entries.")
    constructors: list[ConstructorPrice] = Field(description="Constructor price entries.")
