"""MotoGP data via motogp.pulselive.com (reverse-engineered, free)."""
import httpx

_BASE = "https://api.motogp.pulselive.com/motogp/v1/results"

# Season UUID map (fetched once, hardcoded for stability)
SEASON_UUIDS = {
    2026: "e88b4e43-2209-47aa-8e83-0e0b1cedde6e",
    2025: "ae6c6f0d-c652-44f8-94aa-420fc5b3dab4",
    2024: "dd12382e-1d9f-46ee-a5f7-c5104db28e43",
    2023: "db8dc197-c7b2-4c1b-b3a4-6dc534c023ef",
    2022: "db8dc197-c7b2-4c1b-b3a4-6dc534c014ef",
}

# Category UUIDs — MotoGP, Moto2, Moto3
CATEGORY_UUIDS = {
    "MotoGP": "e8c110ad-64aa-4e8e-8a86-f2f152f6a942",
    "Moto2":  "549640b8-fd9c-4245-acfd-60e4bc38b25c",
    "Moto3":  "954f7e65-2ef2-4423-b949-4961cc603e45",
}

MANUFACTURER_COLOR = {
    "Ducati":   "#cc0000",
    "Aprilia":  "#006633",
    "Honda":    "#cc3300",
    "KTM":      "#ff6a00",
    "Yamaha":   "#003087",
    "Suzuki":   "#004b8d",
}

_HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}


async def get_standings(year: int = 2026, category: str = "MotoGP") -> list[dict]:
    season_uuid = SEASON_UUIDS.get(year)
    cat_uuid = CATEGORY_UUIDS.get(category)
    if not season_uuid or not cat_uuid:
        return []

    url = f"{_BASE}/standings?seasonUuid={season_uuid}&categoryUuid={cat_uuid}"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, headers=_HEADERS)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    riders = []
    classification = data.get("classification", [])
    max_pts = classification[0]["points"] if classification else 1

    for entry in classification:
        rider = entry.get("rider", {})
        team = entry.get("team", {})
        constructor = entry.get("constructor", {})
        manufacturer = constructor.get("name", "")
        pos = entry.get("position", 99)
        pts = entry.get("points", 0)
        wins = entry.get("race_wins", 0)

        full_name = rider.get("full_name", "")
        last = full_name.split()[-1] if full_name else "?"
        code = last[:3].upper()
        country = rider.get("country", {}).get("iso", "")
        number = rider.get("number", "")

        riders.append({
            "series":       "motogp",
            "category":     category,
            "pos":          pos,
            "number":       str(number),
            "full_name":    full_name,
            "last_name":    last,
            "code":         code,
            "team":         team.get("name", ""),
            "manufacturer": manufacturer,
            "color":        MANUFACTURER_COLOR.get(manufacturer, "#888"),
            "country":      country,
            "points":       pts,
            "wins":         wins,
            "podiums":      entry.get("podiums", 0),
            "max_pts":      max_pts,
            "year":         year,
        })

    return riders
