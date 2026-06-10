import pytest
from lapwise.routes.v1.fantasy.prices import fantasy_prices


@pytest.mark.asyncio
async def test_fantasy_prices_has_20_drivers():
    result = await fantasy_prices()
    assert len(result.drivers) == 20


@pytest.mark.asyncio
async def test_fantasy_prices_has_10_constructors():
    result = await fantasy_prices()
    assert len(result.constructors) == 10


@pytest.mark.asyncio
async def test_fantasy_prices_driver_price_range():
    result = await fantasy_prices()
    for driver in result.drivers:
        assert 3.0 <= driver.price_millions <= 34.0


@pytest.mark.asyncio
async def test_fantasy_prices_constructor_price_range():
    result = await fantasy_prices()
    for constructor in result.constructors:
        assert 3.0 <= constructor.price_millions <= 34.0
