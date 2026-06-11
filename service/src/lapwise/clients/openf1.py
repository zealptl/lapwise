"""Async HTTP client for the OpenF1 API."""

import asyncio
import logging
import time
from typing import Any, TypeVar

import httpx

from lapwise.clients.errors import UpstreamError
from lapwise.clients.filters import translate_filters
from lapwise.config import Settings

T = TypeVar("T")
logger = logging.getLogger("lapwise.clients.openf1")

_BODY_EXCERPT_LIMIT = 300
# OpenF1 enforces 3 requests/second; stay safely under that ceiling.
_OPENF1_RATE_LIMIT = 3.0
_429_RETRY_DELAYS = (1.0, 2.0, 4.0)  # seconds between retries on 429


class _RateLimiter:
    """Leaky-bucket rate limiter that spaces requests evenly across a 1-second window."""

    def __init__(self, rate: float) -> None:
        self._interval = 1.0 / rate
        self._next_allowed: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if now < self._next_allowed:
                await asyncio.sleep(self._next_allowed - now)
            self._next_allowed = max(time.monotonic(), self._next_allowed) + self._interval


class OpenF1Client:
    def __init__(self, settings: Settings) -> None:
        timeout = httpx.Timeout(settings.openf1_timeout_seconds)
        self._base_url = settings.openf1_base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)
        self._rate_limiter = _RateLimiter(_OPENF1_RATE_LIMIT)

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

        for attempt, retry_delay in enumerate((*_429_RETRY_DELAYS, None)):
            await self._rate_limiter.acquire()

            logger.debug("GET %s params=%s", url, params)
            t0 = time.monotonic()
            try:
                response = await self._client.get(url, params=params)
            except httpx.TimeoutException as exc:
                logger.warning("GET %s timed out", url)
                raise UpstreamError("gateway_timeout") from exc
            except httpx.HTTPError as exc:
                logger.warning("GET %s HTTP error: %s", url, exc)
                raise UpstreamError("bad_gateway") from exc

            elapsed_ms = (time.monotonic() - t0) * 1000
            status = response.status_code
            logger.debug("GET %s → %d (%.1fms)", url, status, elapsed_ms)

            if status == 429 and retry_delay is not None:
                logger.warning("GET %s → 429, retrying in %.1fs (attempt %d)", url, retry_delay, attempt + 1)
                await asyncio.sleep(retry_delay)
                continue

            break

        if status == 404:
            logger.debug("GET %s → 404 (no data for these filters)", url)
            return []

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
