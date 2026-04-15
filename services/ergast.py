"""Ergast API — F1 歷史數據（已部分停服，改用 OpenF1 補充）"""
import aiohttp
import json
from datetime import datetime, timedelta
from config import ERGAST_BASE, OPENF1_BASE
from database import get_db

CACHE_TTL = 3600


async def _get_cached(key: str):
    db = await get_db()
    row = await db.execute_fetchall(
        "SELECT data, cached_at FROM race_cache WHERE key = ?", (key,)
    )
    await db.close()
    if row:
        cached_at = datetime.fromisoformat(row[0][1])
        if datetime.now() - cached_at < timedelta(seconds=CACHE_TTL):
            return json.loads(row[0][0])
    return None


async def _set_cache(key: str, data):
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO race_cache (key, data, cached_at) VALUES (?, ?, ?)",
        (key, json.dumps(data), datetime.now().isoformat()),
    )
    await db.commit()
    await db.close()


async def _fetch_openf1(endpoint: str, params: dict = None):
    cache_key = f"of1:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{OPENF1_BASE}{endpoint}", params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json()
                await _set_cache(cache_key, data)
                return data
    return []


async def _fetch_ergast(path: str) -> dict:
    """Try Ergast, return empty on failure (service partially down)."""
    cache_key = f"ergast:{path}"
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached
    url = f"{ERGAST_BASE}/{path}.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if text.strip():
                        data = json.loads(text)
                        result = data.get("MRData", {})
                        await _set_cache(cache_key, result)
                        return result
    except Exception:
        pass
    return {}


async def get_season_schedule(year: int = None):
    """Get race schedule — use OpenF1 sessions."""
    from services import openf1
    sessions = await openf1.get_sessions(year or datetime.now().year)
    races = []
    for i, s in enumerate(sessions):
        races.append({
            "round": str(i + 1),
            "season": str(s.get("year", datetime.now().year)),
            "raceName": s.get("meeting_name", s.get("session_name", "")),
            "date": (s.get("date_start", "") or "")[:10],
            "Circuit": {
                "circuitName": s.get("circuit_short_name", ""),
                "Location": {"country": s.get("country_name", "")},
            },
        })
    return races


async def get_race_results(year: int, round_num: int):
    """Try Ergast for historical results."""
    data = await _fetch_ergast(f"{year}/{round_num}/results")
    races = data.get("RaceTable", {}).get("Races", [])
    return races[0] if races else {}


async def get_driver_standings(year: int = None):
    """Get driver standings — try Ergast, fallback to empty."""
    y = year or datetime.now().year
    data = await _fetch_ergast(f"{y}/driverStandings")
    lists = data.get("StandingsTable", {}).get("StandingsLists", [])
    return lists[0].get("DriverStandings", []) if lists else []


async def get_constructor_standings(year: int = None):
    """Get constructor standings."""
    y = year or datetime.now().year
    data = await _fetch_ergast(f"{y}/constructorStandings")
    lists = data.get("StandingsTable", {}).get("StandingsLists", [])
    return lists[0].get("ConstructorStandings", []) if lists else []


async def get_driver_results(driver_id: str, year: int = None):
    """Get driver race results from Ergast."""
    y = year or datetime.now().year
    data = await _fetch_ergast(f"{y}/drivers/{driver_id}/results")
    return data.get("RaceTable", {}).get("Races", [])


async def get_qualifying_results(year: int, round_num: int):
    data = await _fetch_ergast(f"{year}/{round_num}/qualifying")
    races = data.get("RaceTable", {}).get("Races", [])
    return races[0] if races else {}


async def get_all_drivers(year: int = None):
    """Get all drivers — use OpenF1 as primary source."""
    drivers = await _fetch_openf1("/drivers", {"session_key": "latest"})
    # Deduplicate by driver_number
    seen = set()
    unique = []
    for d in drivers:
        num = d.get("driver_number")
        if num not in seen:
            seen.add(num)
            unique.append({
                "driverId": d.get("name_acronym", "").lower(),
                "givenName": d.get("first_name", ""),
                "familyName": d.get("last_name", ""),
                "permanentNumber": str(d.get("driver_number", "")),
                "nationality": d.get("country_code", ""),
                "team": d.get("team_name", ""),
                "team_colour": d.get("team_colour", ""),
                "headshot_url": d.get("headshot_url", ""),
            })
    return unique


async def get_all_constructors(year: int = None):
    """Get constructors from OpenF1 drivers data."""
    drivers = await _fetch_openf1("/drivers", {"session_key": "latest"})
    teams = {}
    for d in drivers:
        team = d.get("team_name", "")
        if team and team not in teams:
            teams[team] = {
                "constructorId": team.lower().replace(" ", "_"),
                "name": team,
                "nationality": "",
                "team_colour": d.get("team_colour", ""),
            }
    return list(teams.values())
