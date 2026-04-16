"""routes/historical.py — Real 2024 F1 historical data endpoints"""
from fastapi import APIRouter
from services.historical_data import get_driver_stats, get_race_history

router = APIRouter(prefix="/api", tags=["historical"])


@router.get("/drivers/stats")
async def driver_stats():
    """2024 season stats for all drivers: wins, podiums, qualifying avg, last-5 trend, Jeddah history."""
    stats = await get_driver_stats()
    return {"season": 2024, "source": "ergast+fallback", "drivers": stats}


@router.get("/races/history")
async def race_history(limit: int = 10):
    """Last N race results from 2024 season (default 10)."""
    races = await get_race_history(min(limit, 24))
    return {"season": 2024, "count": len(races), "races": races}
