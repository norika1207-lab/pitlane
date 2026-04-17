"""routes/historical.py — Real 5-year F1 historical data endpoints"""
from fastapi import APIRouter
from services.historical_data import (
    get_driver_stats, get_race_history,
    get_season_races, get_season_standings, get_season_meta,
    get_all_seasons, get_driver_career,
)

router = APIRouter(prefix="/api", tags=["historical"])


@router.get("/drivers/stats")
async def driver_stats():
    """2024 season stats for all drivers: wins, podiums, qualifying avg, last-5 trend."""
    stats = await get_driver_stats()
    return {"season": 2024, "source": "jolpica+fallback", "drivers": stats}


@router.get("/races/history")
async def race_history(limit: int = 10):
    """Last N race results from 2024 season (default 10)."""
    races = await get_race_history(min(limit, 24))
    return {"season": 2024, "count": len(races), "races": races}


@router.get("/history/seasons")
async def all_seasons():
    """Overview of all 5 seasons (2020-2024) with champions."""
    seasons = await get_all_seasons()
    return {"seasons": seasons}


@router.get("/history/season/{year}")
async def season_detail(year: int):
    """Full season data: meta, top-10 standings, all race results."""
    if year not in range(2020, 2025):
        return {"error": "Only 2020-2024 available"}
    races = await get_season_races(year)
    standings = await get_season_standings(year)
    meta = await get_season_meta(year)
    return {
        "year": year,
        "meta": meta,
        "standings": standings[:10],
        "races": races,
    }


@router.get("/history/standings/{year}")
async def season_standings(year: int):
    """Championship standings for a given year."""
    if year not in range(2020, 2025):
        return {"error": "Only 2020-2024 available"}
    standings = await get_season_standings(year)
    return {"year": year, "standings": standings}


@router.get("/history/driver/{driver_id}")
async def driver_career(driver_id: str):
    """Career stats across all 5 seasons for a driver (e.g. 'max_verstappen')."""
    return await get_driver_career(driver_id)
