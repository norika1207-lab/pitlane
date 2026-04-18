"""Motorsport routes — MotoGP + NASCAR driver/card endpoints."""
from fastapi import APIRouter, Query
from services.motogp import get_standings as motogp_standings, SEASON_UUIDS as MOTOGP_SEASONS
from services.nascar import get_drivers as nascar_drivers

router = APIRouter(prefix="/api/motorsport", tags=["motorsport"])


@router.get("/motogp/drivers")
async def motogp_drivers(
    year: int = Query(default=2026),
    category: str = Query(default="MotoGP"),
):
    drivers = await motogp_standings(year, category)
    return {
        "series": "motogp",
        "category": category,
        "year": year,
        "drivers": drivers,
        "available_years": sorted(MOTOGP_SEASONS.keys(), reverse=True),
    }


@router.get("/nascar/drivers")
async def get_nascar_drivers(year: int = Query(default=2025)):
    drivers = nascar_drivers(year)
    return {
        "series": "nascar",
        "category": "Cup Series",
        "year": year,
        "drivers": drivers,
        "available_years": [2025],
    }
