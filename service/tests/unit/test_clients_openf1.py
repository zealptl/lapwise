"""Unit tests for lapwise.clients.openf1.OpenF1Client using respx."""

import httpx
import pytest
import respx
from pydantic import BaseModel

from lapwise.clients.errors import UpstreamError
from lapwise.clients.openf1 import OpenF1Client
from lapwise.config import Settings


class _Driver(BaseModel):
    driver_number: int
    full_name: str


def _make_client(base_url: str = "https://api.openf1.org/v1") -> OpenF1Client:
    settings = Settings(openf1_base_url=base_url, openf1_timeout_seconds=5.0)
    return OpenF1Client(settings)


@respx.mock
async def test_200_returns_list_of_parsed_models() -> None:
    payload = [{"driver_number": 1, "full_name": "Max Verstappen"}]
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(200, json=payload)
    )

    client = _make_client()
    result = await client.get("drivers", _Driver)
    await client.aclose()

    assert len(result) == 1
    assert result[0].driver_number == 1
    assert result[0].full_name == "Max Verstappen"


@respx.mock
async def test_5xx_raises_bad_gateway() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    err = exc_info.value
    assert err.category == "bad_gateway"
    assert err.upstream_status == 503


@respx.mock
async def test_404_returns_empty_list() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(404, text="Not Found")
    )

    client = _make_client()
    result = await client.get("drivers", _Driver)
    await client.aclose()

    assert result == []


@respx.mock
async def test_4xx_other_raises_forwarded() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(403, text="Forbidden")
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    err = exc_info.value
    assert err.category == "forwarded"
    assert err.upstream_status == 403


@respx.mock
async def test_timeout_raises_gateway_timeout() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        side_effect=httpx.TimeoutException("timed out")
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    assert exc_info.value.category == "gateway_timeout"


@respx.mock
async def test_malformed_json_raises_bad_gateway() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(200, content=b"not-json!!!")
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    err = exc_info.value
    assert err.category == "bad_gateway"
    assert err.upstream_message == "decode failure"


@respx.mock
async def test_non_list_json_raises_bad_gateway() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(200, json={"error": "unexpected"})
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    err = exc_info.value
    assert err.category == "bad_gateway"
    assert err.upstream_message == "decode failure"


@respx.mock
async def test_filter_translation_visible_in_upstream_url() -> None:
    """Verify that translated filter params appear in the upstream request URL."""
    route = respx.get("https://api.openf1.org/v1/drivers").mock(
        return_value=httpx.Response(200, json=[])
    )

    client = _make_client()
    await client.get("drivers", _Driver, driver_number=44, session_key=9165)
    await client.aclose()

    assert route.called
    request = route.calls.last.request
    url_str = str(request.url)
    assert "driver_number=44" in url_str
    assert "session_key=9165" in url_str


@respx.mock
async def test_connect_error_raises_bad_gateway() -> None:
    respx.get("https://api.openf1.org/v1/drivers").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = _make_client()
    with pytest.raises(UpstreamError) as exc_info:
        await client.get("drivers", _Driver)
    await client.aclose()

    assert exc_info.value.category == "bad_gateway"
