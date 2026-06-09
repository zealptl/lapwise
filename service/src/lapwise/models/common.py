"""Common response models shared across the Lapwise API."""

from pydantic import BaseModel, Field


class ErrorEnvelope(BaseModel):
    """Standard error body returned for upstream error responses."""

    detail: str = Field(description="Human-readable summary of the error.")
    upstream_status: int | None = Field(
        default=None,
        description="HTTP status code returned by the upstream OpenF1 API, if available.",
    )
    upstream_message: str | None = Field(
        default=None,
        description="Excerpt of the upstream response body, if available.",
    )
