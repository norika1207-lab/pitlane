from fastapi import APIRouter
from services import ergast, openf1
from services.race_names import get_race_name, get_circuit_type, get_circuit_type_raw
from datetime import datetime

router = APIRouter(prefix="/api/races", tags=["races"])


@router.get("/current")
async def current_race():
    """Get current or next race info."""
    session = await openf1.get_current_session()
    if session:
        circuit = session.get("circuit_short_name", "")
        country = session.get("country_name", "")
        race_name = get_race_name(circuit, country, session.get("meeting_name", ""))
        return {
            "source": "openf1",
            "session_key": session.get("session_key"),
            "race_name": race_name,
            "circuit": circuit,
            "circuit_type": get_circuit_type(circuit),
            "circuit_type_raw": get_circuit_type_raw(circuit),
            "country": country,
            "date": session.get("date_start", ""),
            "location": session.get("location", ""),
            "year": session.get("year", datetime.now().year),
            "race_id": f"{session.get('year', 2026)}_{session.get('session_key', '')}",
        }

    schedule = await ergast.get_season_schedule()
    now = datetime.now().isoformat()
    upcoming = [r for r in schedule if r.get("date", "") >= now[:10]]
    if upcoming:
        race = upcoming[0]
        circuit = race.get("Circuit", {}).get("circuitName", "")
        country = race.get("Circuit", {}).get("Location", {}).get("country", "")
        return {
            "source": "ergast",
            "race_id": f"{race.get('season')}_{race.get('round')}",
            "race_name": get_race_name(circuit, country, race.get("raceName", "")),
            "circuit": circuit,
            "circuit_type": get_circuit_type(circuit),
            "country": country,
            "date": race.get("date", ""),
            "round": int(race.get("round", 0)),
            "year": int(race.get("season", datetime.now().year)),
        }

    return {"message": "No upcoming races found", "season_over": True}


@router.get("/schedule")
async def race_schedule():
    """Get full season schedule."""
    year = datetime.now().year
    sessions = await openf1.get_sessions(year)

    races = []
    for i, s in enumerate(sessions):
        circuit = s.get("circuit_short_name", "")
        country = s.get("country_name", "")
        races.append({
            "round": i + 1,
            "race_name": get_race_name(circuit, country),
            "circuit": circuit,
            "circuit_type": get_circuit_type(circuit),
            "country": country,
            "date": (s.get("date_start", "") or "")[:10],
            "race_id": f"{year}_{s.get('session_key', '')}",
            "session_key": s.get("session_key"),
        })
    return {"year": year, "races": races}


@router.get("/{year}/{round_num}/results")
async def race_results(year: int, round_num: int):
    """Get results for a specific race (historical via Ergast)."""
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


@router.get("/weather/{session_key}")
async def race_weather(session_key: int):
    """Get weather data for a session."""
    weather = await openf1.get_weather(session_key)
    if not weather:
        return {"available": False}
    # Return latest weather reading
    latest = weather[-1] if weather else {}
    return {
        "available": True,
        "air_temperature": latest.get("air_temperature"),
        "track_temperature": latest.get("track_temperature"),
        "humidity": latest.get("humidity"),
        "pressure": latest.get("pressure"),
        "rainfall": latest.get("rainfall", 0),
        "wind_speed": latest.get("wind_speed"),
        "wind_direction": latest.get("wind_direction"),
    }
