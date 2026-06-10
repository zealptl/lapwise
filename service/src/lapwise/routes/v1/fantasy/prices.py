"""GET /v1/fantasy/prices - 2025 F1 Fantasy price list.

Last updated: 2025-06-09
TODO: Update after each race week when official prices change.
"""

from fastapi import APIRouter

from lapwise.models.fantasy_prices import ConstructorPrice, DriverPrice, FantasyPrices

router = APIRouter()

_PRICES_2025 = FantasyPrices(
    season=2025,
    last_updated="2025-06-09",
    drivers=[
        DriverPrice(driver_number=1,  full_name="Max Verstappen",       team_name="Red Bull Racing",  price_millions=30.0),
        DriverPrice(driver_number=4,  full_name="Lando Norris",         team_name="McLaren",          price_millions=28.5),
        DriverPrice(driver_number=16, full_name="Charles Leclerc",      team_name="Ferrari",          price_millions=26.5),
        DriverPrice(driver_number=63, full_name="George Russell",       team_name="Mercedes",         price_millions=25.0),
        DriverPrice(driver_number=44, full_name="Lewis Hamilton",       team_name="Ferrari",          price_millions=24.5),
        DriverPrice(driver_number=81, full_name="Oscar Piastri",        team_name="McLaren",          price_millions=22.5),
        DriverPrice(driver_number=55, full_name="Carlos Sainz",        team_name="Williams",          price_millions=20.0),
        DriverPrice(driver_number=14, full_name="Fernando Alonso",      team_name="Aston Martin",     price_millions=16.0),
        DriverPrice(driver_number=22, full_name="Yuki Tsunoda",         team_name="Red Bull Racing",  price_millions=13.5),
        DriverPrice(driver_number=18, full_name="Lance Stroll",         team_name="Aston Martin",     price_millions=10.0),
        DriverPrice(driver_number=10, full_name="Pierre Gasly",         team_name="Alpine",           price_millions=10.5),
        DriverPrice(driver_number=31, full_name="Esteban Ocon",         team_name="Haas",             price_millions=8.5),
        DriverPrice(driver_number=23, full_name="Alexander Albon",      team_name="Williams",         price_millions=9.5),
        DriverPrice(driver_number=27, full_name="Nico Hulkenberg",      team_name="Sauber",           price_millions=9.0),
        DriverPrice(driver_number=87, full_name="Oliver Bearman",       team_name="Haas",             price_millions=7.5),
        DriverPrice(driver_number=7,  full_name="Jack Doohan",          team_name="Alpine",           price_millions=6.5),
        DriverPrice(driver_number=5,  full_name="Gabriel Bortoleto",    team_name="Sauber",           price_millions=6.0),
        DriverPrice(driver_number=30, full_name="Liam Lawson",          team_name="Racing Bulls",     price_millions=8.0),
        DriverPrice(driver_number=6,  full_name="Isack Hadjar",         team_name="Racing Bulls",     price_millions=5.5),
        DriverPrice(driver_number=12, full_name="Andrea Kimi Antonelli",team_name="Mercedes",         price_millions=15.0),
    ],
    constructors=[
        ConstructorPrice(team_name="McLaren",         price_millions=33.5),
        ConstructorPrice(team_name="Ferrari",         price_millions=31.0),
        ConstructorPrice(team_name="Red Bull Racing", price_millions=28.5),
        ConstructorPrice(team_name="Mercedes",        price_millions=26.0),
        ConstructorPrice(team_name="Williams",        price_millions=14.5),
        ConstructorPrice(team_name="Aston Martin",    price_millions=13.0),
        ConstructorPrice(team_name="Alpine",          price_millions=10.5),
        ConstructorPrice(team_name="Racing Bulls",    price_millions=10.0),
        ConstructorPrice(team_name="Haas",            price_millions=9.0),
        ConstructorPrice(team_name="Sauber",          price_millions=7.5),
    ],
)


@router.get(
    "/prices",
    response_model=FantasyPrices,
    summary="F1 Fantasy prices",
    description="Returns the current 2025 F1 Fantasy driver and constructor price list. No authentication required.",
)
async def fantasy_prices() -> FantasyPrices:
    """Return the hardcoded 2025 F1 Fantasy price list."""
    return _PRICES_2025
