"""OpenF1 API — 當季即時 F1 數據"""
import aiohttp
import json
from datetime import datetime, timedelta
from config import OPENF1_BASE
from database import get_db

CACHE_TTL = 300  # 5 minutes


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


async def _fetch(endpoint: str, params: dict = None) -> list | dict:
    cache_key = f"openf1:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
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


async def get_sessions(year: int = None):
    """Get race sessions for the year."""
    params = {}
    if year:
        params["year"] = year
    sessions = await _fetch("/sessions", params)
    # Filter to race sessions only
    races = [s for s in sessions if s.get("session_type") == "Race"]
    return races


async def get_current_session():
    """Get the most recent or upcoming race session."""
    now = datetime.now()
    sessions = await get_sessions(now.year)
    if not sessions:
        return None

    # Find the closest session (past or future)
    upcoming = []
    past = []
    for s in sessions:
        session_date = s.get("date_start", "")
        if session_date:
            if session_date > now.isoformat():
                upcoming.append(s)
            else:
                past.append(s)

    # Return the nearest upcoming, or the most recent past
    if upcoming:
        return upcoming[0]
    elif past:
        return past[-1]
    return sessions[-1] if sessions else None


async def get_drivers(session_key: int = None):
    """Get drivers for a session."""
    params = {}
    if session_key:
        params["session_key"] = session_key
    return await _fetch("/drivers", params)


async def get_positions(session_key: int):
    """Get position data for a session."""
    return await _fetch("/position", {"session_key": session_key})


async def get_laps(session_key: int, driver_number: int = None):
    """Get lap data."""
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    return await _fetch("/laps", params)


async def get_pit_stops(session_key: int):
    """Get pit stop data."""
    return await _fetch("/pit", {"session_key": session_key})


async def get_weather(session_key: int):
    """Get weather data."""
    return await _fetch("/weather", {"session_key": session_key})
