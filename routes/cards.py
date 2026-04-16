from fastapi import APIRouter
from services import ergast, openf1
from services.card_engine import calculate_driver_card, calculate_constructor_card, calculate_odds
from services.driver_skills import get_driver_skills
from services.odds_engine import calculate_winner_odds
from datetime import datetime

router = APIRouter(prefix="/api", tags=["cards"])


@router.get("/drivers")
async def list_drivers():
    """List all current season drivers with basic info."""
    drivers = await ergast.get_all_drivers()

    if not drivers:
        return {"year": datetime.now().year, "drivers": []}

    result = []
    for d in drivers:
        result.append({
            "driver_id": d.get("driverId", ""),
            "name": f"{d.get('givenName', '')} {d.get('familyName', '')}",
            "number": d.get("permanentNumber", ""),
            "nationality": d.get("nationality", ""),
            "team": d.get("team", ""),
            "team_colour": d.get("team_colour", ""),
            "headshot_url": d.get("headshot_url", ""),
            "points": 0,
            "championship_pos": 0,
            "wins": 0,
        })

    return {"year": datetime.now().year, "drivers": result}


@router.get("/drivers/{driver_id}/card")
async def driver_card(driver_id: str):
    """Get full driver card with calculated stats."""
    drivers = await ergast.get_all_drivers()

    name = driver_id
    nationality = ""
    number = ""
    team = ""
    team_colour = ""
    headshot = ""

    for d in drivers:
        if d.get("driverId", "").lower() == driver_id.lower():
            name = f"{d.get('givenName', '')} {d.get('familyName', '')}"
            nationality = d.get("nationality", "")
            number = d.get("permanentNumber", "")
            team = d.get("team", "")
            team_colour = d.get("team_colour", "")
            headshot = d.get("headshot_url", "")
            break

    stats = await calculate_driver_card(driver_id)
    odds = calculate_winner_odds(driver_id)
    skills = get_driver_skills(driver_id)

    return {
        "driver_id": driver_id,
        "name": name,
        "number": number,
        "nationality": nationality,
        "team": team,
        "team_colour": team_colour,
        "headshot_url": headshot,
        "year": datetime.now().year,
        "stats": stats,
        "odds": odds,
        "skills": skills,
    }


@router.get("/constructors")
async def list_constructors():
    """List all constructors from OpenF1."""
    constructors = await ergast.get_all_constructors()

    result = []
    for i, c in enumerate(constructors):
        result.append({
            "constructor_id": c.get("constructorId", ""),
            "name": c.get("name", ""),
            "nationality": c.get("nationality", ""),
            "team_colour": c.get("team_colour", ""),
            "points": 0,
            "position": i + 1,
            "wins": 0,
        })

    return {"year": datetime.now().year, "constructors": result}


@router.get("/constructors/{constructor_id}/card")
async def constructor_card(constructor_id: str):
    """Get constructor card with stats."""
    constructors = await ergast.get_all_constructors()

    name = constructor_id
    nationality = ""
    team_colour = ""
    position = 5

    for i, c in enumerate(constructors):
        if c.get("constructorId") == constructor_id:
            name = c.get("name", "")
            nationality = c.get("nationality", "")
            team_colour = c.get("team_colour", "")
            position = i + 1
            break

    stats = await calculate_constructor_card(constructor_id)

    return {
        "constructor_id": constructor_id,
        "name": name,
        "nationality": nationality,
        "team_colour": team_colour,
        "year": datetime.now().year,
        "stats": stats,
    }
