"""Async HTTP client for the OpenF1 API."""

from typing import Any, TypeVar

import httpx

from lapwise.clients.errors import UpstreamError
from lapwise.clients.filters import translate_filters
from lapwise.config import Settings

T = TypeVar("T")

_BODY_EXCERPT_LIMIT = 300


class OpenF1Client:
    def __init__(self, settings: Settings) -> None:
        timeout = httpx.Timeout(settings.openf1_timeout_seconds)
        self._base_url = settings.openf1_base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get(self, path: str, model: type[T], **filters: Any) -> list[T]:
        """Fetch a list of resources from OpenF1 and return parsed models.

        Args:
            path: The OpenF1 endpoint path (e.g. ``drivers``).
            model: A Pydantic model class used to validate each item.
            **filters: Filter parameters in the wrapper's hybrid syntax.

        Returns:
            A list of validated model instances.

        Raises:
            UpstreamError: On HTTP errors, timeouts, or decode failures.
        """
        url = f"{self._base_url}/{path}"
        params: list[tuple[str, str | int | float | bool | None]] = [
            *translate_filters(dict(filters))
        ]

        try:
            response = await self._client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise UpstreamError("gateway_timeout") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("bad_gateway") from exc

        status = response.status_code

        if status >= 500:
            excerpt = response.text[:_BODY_EXCERPT_LIMIT]
            raise UpstreamError(
                "bad_gateway",
                upstream_status=status,
                upstream_message=excerpt,
            )

        if status >= 400:
            excerpt = response.text[:_BODY_EXCERPT_LIMIT]
            raise UpstreamError(
                "forwarded",
                upstream_status=status,
                upstream_message=excerpt,
            )

        try:
            body = response.json()
        except Exception as exc:
            raise UpstreamError("bad_gateway", upstream_message="decode failure") from exc

        if not isinstance(body, list):
            raise UpstreamError("bad_gateway", upstream_message="decode failure")

        # model is expected to be a Pydantic BaseModel subclass
        return [model.model_validate(item) for item in body]  # type: ignore[attr-defined]

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
