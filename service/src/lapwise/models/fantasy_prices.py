"""Pydantic models for Fantasy F1 driver and constructor prices."""

from pydantic import BaseModel, Field


class DriverPrice(BaseModel):
    """Fantasy price entry for a single driver."""

    driver_number: int = Field(description="Official driver racing number.")
    full_name: str = Field(description="Driver's full display name.")
    team_name: str = Field(description="Constructor name the driver races for.")
    price_millions: float = Field(description="Fantasy price in millions (e.g. 30.5 = $30.5M).")


class ConstructorPrice(BaseModel):
    """Fantasy price entry for a single constructor."""

    team_name: str = Field(description="Constructor name.")
    price_millions: float = Field(description="Fantasy price in millions (e.g. 30.5 = $30.5M).")


class FantasyPrices(BaseModel):
    """Full fantasy price list for a given season."""

    season: int = Field(description="Championship season year.")
    last_updated: str = Field(
        description="ISO 8601 date string indicating when prices were last updated."
    )
    drivers: list[DriverPrice] = Field(description="Fantasy prices for all drivers.")
    constructors: list[ConstructorPrice] = Field(
        description="Fantasy prices for all constructors."
    )
