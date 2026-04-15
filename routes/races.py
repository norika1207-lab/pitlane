from fastapi import APIRouter
from services import ergast, openf1
from datetime import datetime

router = APIRouter(prefix="/api/races", tags=["races"])


@router.get("/current")
async def current_race():
    """Get current or next race info."""
    # Try OpenF1 first for live data
    session = await openf1.get_current_session()
    if session:
        return {
            "source": "openf1",
            "session_key": session.get("session_key"),
            "race_name": session.get("session_name", ""),
            "circuit": session.get("circuit_short_name", ""),
            "country": session.get("country_name", ""),
            "date": session.get("date_start", ""),
            "location": session.get("location", ""),
            "year": session.get("year", datetime.now().year),
        }

    # Fallback to Ergast schedule
    schedule = await ergast.get_season_schedule()
    now = datetime.now().isoformat()
    upcoming = [r for r in schedule if r.get("date", "") >= now[:10]]
    if upcoming:
        race = upcoming[0]
        return {
            "source": "ergast",
            "race_id": f"{race.get('season')}_{race.get('round')}",
            "race_name": race.get("raceName", ""),
            "circuit": race.get("Circuit", {}).get("circuitName", ""),
            "country": race.get("Circuit", {}).get("Location", {}).get("country", ""),
            "date": race.get("date", ""),
            "round": int(race.get("round", 0)),
            "year": int(race.get("season", datetime.now().year)),
        }

    return {"message": "No upcoming races found", "season_over": True}


@router.get("/schedule")
async def race_schedule():
    """Get full season schedule."""
    year = datetime.now().year
    schedule = await ergast.get_season_schedule(year)
    races = []
    for race in schedule:
        races.append({
            "round": int(race.get("round", 0)),
            "race_name": race.get("raceName", ""),
            "circuit": race.get("Circuit", {}).get("circuitName", ""),
            "country": race.get("Circuit", {}).get("Location", {}).get("country", ""),
            "date": race.get("date", ""),
            "race_id": f"{race.get('season')}_{race.get('round')}",
        })
    return {"year": year, "races": races}


@router.get("/{year}/{round_num}/results")
async def race_results(year: int, round_num: int):
    """Get results for a specific race."""
    data = await ergast.get_race_results(year, round_num)
    if not data:
        return {"error": "Race results not found"}

    results = []
    for r in data.get("Results", []):
        driver = r.get("Driver", {})
        constructor = r.get("Constructor", {})
        results.append({
            "position": int(r.get("position", 0)),
            "driver_id": driver.get("driverId", ""),
            "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}",
            "constructor": constructor.get("name", ""),
            "grid": int(r.get("grid", 0)),
            "status": r.get("status", ""),
            "points": float(r.get("points", 0)),
            "fastest_lap": r.get("FastestLap", {}).get("Time", {}).get("time", ""),
        })
    return {
        "race_name": data.get("raceName", ""),
        "circuit": data.get("Circuit", {}).get("circuitName", ""),
        "date": data.get("date", ""),
        "results": results,
    }
