"""Pydantic model for OpenF1 /session_result responses."""

from pydantic import BaseModel, Field


class SessionResult(BaseModel):
    """A driver's final classification for a session as returned by OpenF1's /session_result."""

    dnf: bool = Field(description="Whether the driver did not finish (DNF).")
    dns: bool = Field(description="Whether the driver did not start (DNS).")
    dsq: bool = Field(description="Whether the driver was disqualified (DSQ).")
    driver_number: int = Field(description="Car number of the driver.")
    duration: float | list[float] | None = Field(
        default=None,
        description=(
            "Race or sprint finishing time in seconds. "
            "For qualifying, this is an array of three values [Q1, Q2, Q3] in seconds."
        ),
    )
    gap_to_leader: float | str | None = Field(
        default=None,
        description=(
            "Gap to the race leader in seconds. "
            "Lapped finishers appear as a string (e.g. '+1 LAP')."
        ),
    )
    number_of_laps: int | None = Field(
        default=None, description="Number of laps completed by the driver."
    )
    meeting_key: int = Field(description="Unique identifier for the parent meeting.")
    position: int | None = Field(
        default=None, description="Final classified position (1 = winner)."
    )
    session_key: int = Field(description="Unique identifier for the session.")
