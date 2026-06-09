"""Pydantic model for OpenF1 /position responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class Position(BaseModel):
    """A single position record from the OpenF1 /position endpoint.

    Captures a driver's race position at a specific point in time during
    a session. Multiple records may exist per driver per session, reflecting
    position changes throughout the race.

    See https://api.openf1.org/v1/position for the upstream field reference.
    """

    date: datetime = Field(
        description=(
            "UTC timestamp at which this position record was captured. "
            "Positions are sampled at irregular intervals during the session."
        ),
    )
    driver_number: int = Field(
        description=(
            "The permanent race number assigned to the driver "
            "(e.g. 1 for Max Verstappen, 44 for Lewis Hamilton)."
        ),
    )
    meeting_key: int = Field(
        description=(
            "Unique identifier for the meeting (race weekend) to which this "
            "position record belongs."
        ),
    )
    position: int = Field(
        description=(
            "The driver's race position at the time of this record. 1 indicates the lead position."
        ),
    )
    session_key: int = Field(
        description=(
            "Unique identifier for the session (e.g. race, qualifying, practice) "
            "to which this position record belongs."
        ),
    )
