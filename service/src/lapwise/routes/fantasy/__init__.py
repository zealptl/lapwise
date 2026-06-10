"""Fantasy router — F1 Fantasy pricing and recommendation endpoints."""

from fastapi import APIRouter, Depends

from lapwise.deps import get_auth
from lapwise.models.fantasy import ConstructorPrice, DriverPrice, FantasyPrices

router = APIRouter(
    prefix="/v1/fantasy",
    tags=["Fantasy"],
    dependencies=[Depends(get_auth)],
)

_DRIVER_PRICES: list[DriverPrice] = [
    DriverPrice(driver_number=1,  full_name="Max Verstappen",    abbreviation="VER", team="Red Bull Racing",  price_millions=30.0),
    DriverPrice(driver_number=4,  full_name="Lando Norris",      abbreviation="NOR", team="McLaren",          price_millions=28.0),
    DriverPrice(driver_number=16, full_name="Charles Leclerc",   abbreviation="LEC", team="Ferrari",          price_millions=25.0),
    DriverPrice(driver_number=44, full_name="Lewis Hamilton",    abbreviation="HAM", team="Ferrari",          price_millions=24.5),
    DriverPrice(driver_number=63, full_name="George Russell",    abbreviation="RUS", team="Mercedes",         price_millions=22.0),
    DriverPrice(driver_number=81, full_name="Oscar Piastri",     abbreviation="PIA", team="McLaren",          price_millions=22.0),
    DriverPrice(driver_number=55, full_name="Carlos Sainz",      abbreviation="SAI", team="Williams",         price_millions=18.0),
    DriverPrice(driver_number=14, full_name="Fernando Alonso",   abbreviation="ALO", team="Aston Martin",     price_millions=17.5),
    DriverPrice(driver_number=11, full_name="Sergio Perez",      abbreviation="PER", team="Red Bull Racing",  price_millions=17.0),
    DriverPrice(driver_number=23, full_name="Alex Albon",        abbreviation="ALB", team="Williams",         price_millions=9.5),
    DriverPrice(driver_number=22, full_name="Yuki Tsunoda",      abbreviation="TSU", team="RB",               price_millions=9.0),
    DriverPrice(driver_number=10, full_name="Pierre Gasly",      abbreviation="GAS", team="Alpine",           price_millions=9.0),
    DriverPrice(driver_number=31, full_name="Esteban Ocon",      abbreviation="OCO", team="Haas",             price_millions=8.5),
    DriverPrice(driver_number=27, full_name="Nico Hulkenberg",   abbreviation="HUL", team="Sauber",           price_millions=8.0),
    DriverPrice(driver_number=18, full_name="Lance Stroll",      abbreviation="STR", team="Aston Martin",     price_millions=8.0),
    DriverPrice(driver_number=20, full_name="Kevin Magnussen",   abbreviation="MAG", team="Haas",             price_millions=7.5),
    DriverPrice(driver_number=77, full_name="Valtteri Bottas",   abbreviation="BOT", team="Sauber",           price_millions=7.0),
    DriverPrice(driver_number=87, full_name="Oliver Bearman",    abbreviation="BEA", team="Haas",             price_millions=7.0),
    DriverPrice(driver_number=7,  full_name="Jack Doohan",       abbreviation="DOO", team="Alpine",           price_millions=7.0),
    DriverPrice(driver_number=6,  full_name="Isack Hadjar",      abbreviation="HAD", team="RB",               price_millions=7.0),
]

_CONSTRUCTOR_PRICES: list[ConstructorPrice] = [
    ConstructorPrice(name="McLaren",         abbreviation="MCL", price_millions=33.0),
    ConstructorPrice(name="Ferrari",         abbreviation="FER", price_millions=32.0),
    ConstructorPrice(name="Red Bull Racing", abbreviation="RBR", price_millions=30.0),
    ConstructorPrice(name="Mercedes",        abbreviation="MER", price_millions=27.0),
    ConstructorPrice(name="Aston Martin",    abbreviation="AMR", price_millions=14.0),
    ConstructorPrice(name="Williams",        abbreviation="WIL", price_millions=12.0),
    ConstructorPrice(name="Alpine",          abbreviation="ALP", price_millions=10.0),
    ConstructorPrice(name="RB",              abbreviation="RB",  price_millions=9.0),
    ConstructorPrice(name="Haas",            abbreviation="HAS", price_millions=8.5),
    ConstructorPrice(name="Sauber",          abbreviation="SAU", price_millions=7.5),
]

_PRICES = FantasyPrices(drivers=_DRIVER_PRICES, constructors=_CONSTRUCTOR_PRICES)


@router.get(
    "/prices",
    response_model=FantasyPrices,
    summary="2025 F1 Fantasy prices",
    description=(
        "Return the hardcoded 2025 F1 Fantasy prices for all 20 drivers and 10 constructors. "
        "Prices are expressed in millions of dollars and reflect the start-of-season valuations. "
        "This endpoint is the authoritative price source for the LapwiseF1Agent budget "
        "constraint calculations (£100M total team budget)."
    ),
)
async def get_fantasy_prices() -> FantasyPrices:
    return _PRICES
