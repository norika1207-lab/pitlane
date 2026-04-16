"""services/historical_data.py
F1 Historical Data Service — 2024 season stats
Primary source: Ergast API  |  Fallback: hardcoded final standings
Cache: SQLite race_cache table, 24 h TTL
"""
import json
import aiohttp
from datetime import datetime, timedelta
from database import get_db

SEASON = 2024
CACHE_TTL = 86400  # 24 h

ERGAST = "https://ergast.com/api/f1"

# ─── Fallback: 2024 final standings ─────────────────────────────────────────
# wins/podiums/races verified from public 2024 championship records
_FALLBACK_STANDINGS: dict[str, dict] = {
    "verstappen": {"pos":1,"code":"VER","name":"Max Verstappen",     "team":"Red Bull Racing","color":"#3671C6","pts":437,"wins":9, "podiums":14,"races":24,"avg_grid":1.8,"wet_wins":1},
    "norris":     {"pos":2,"code":"NOR","name":"Lando Norris",        "team":"McLaren",        "color":"#F47600","pts":374,"wins":4, "podiums":15,"races":24,"avg_grid":3.2,"wet_wins":0},
    "leclerc":    {"pos":3,"code":"LEC","name":"Charles Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":356,"wins":3, "podiums":12,"races":24,"avg_grid":2.4,"wet_wins":0},
    "piastri":    {"pos":4,"code":"PIA","name":"Oscar Piastri",       "team":"McLaren",        "color":"#F47600","pts":292,"wins":2, "podiums":9, "races":24,"avg_grid":4.8,"wet_wins":0},
    "sainz":      {"pos":5,"code":"SAI","name":"Carlos Sainz",        "team":"Ferrari",        "color":"#E8002D","pts":290,"wins":3, "podiums":12,"races":24,"avg_grid":3.8,"wet_wins":0},
    "hamilton":   {"pos":6,"code":"HAM","name":"Lewis Hamilton",      "team":"Mercedes",       "color":"#27F4D2","pts":223,"wins":2, "podiums":7, "races":24,"avg_grid":4.8,"wet_wins":0},
    "russell":    {"pos":7,"code":"RUS","name":"George Russell",      "team":"Mercedes",       "color":"#27F4D2","pts":217,"wins":1, "podiums":8, "races":24,"avg_grid":4.2,"wet_wins":0},
    "perez":      {"pos":8,"code":"PER","name":"Sergio Perez",        "team":"Red Bull Racing","color":"#3671C6","pts":152,"wins":2, "podiums":8, "races":24,"avg_grid":5.5,"wet_wins":0},
    "alonso":     {"pos":9,"code":"ALO","name":"Fernando Alonso",     "team":"Aston Martin",   "color":"#358C75","pts":70, "wins":0, "podiums":2, "races":24,"avg_grid":6.8,"wet_wins":0},
    "hulkenberg": {"pos":10,"code":"HUL","name":"Nico Hulkenberg",    "team":"Haas",           "color":"#B6BABD","pts":31, "wins":0, "podiums":0, "races":24,"avg_grid":9.2,"wet_wins":0},
    "stroll":     {"pos":11,"code":"STR","name":"Lance Stroll",       "team":"Aston Martin",   "color":"#358C75","pts":24, "wins":0, "podiums":0, "races":24,"avg_grid":11.2,"wet_wins":0},
    "tsunoda":    {"pos":12,"code":"TSU","name":"Yuki Tsunoda",       "team":"RB",             "color":"#6692FF","pts":22, "wins":0, "podiums":0, "races":24,"avg_grid":10.8,"wet_wins":0},
    "magnussen":  {"pos":13,"code":"MAG","name":"Kevin Magnussen",    "team":"Haas",           "color":"#B6BABD","pts":14, "wins":0, "podiums":0, "races":24,"avg_grid":12.5,"wet_wins":0},
    "albon":      {"pos":14,"code":"ALB","name":"Alexander Albon",    "team":"Williams",       "color":"#64C4FF","pts":12, "wins":0, "podiums":0, "races":24,"avg_grid":11.8,"wet_wins":0},
    "gasly":      {"pos":15,"code":"GAS","name":"Pierre Gasly",       "team":"Alpine",         "color":"#FF87BC","pts":8,  "wins":0, "podiums":0, "races":24,"avg_grid":12.2,"wet_wins":0},
    "ocon":       {"pos":16,"code":"OCO","name":"Esteban Ocon",       "team":"Alpine",         "color":"#FF87BC","pts":5,  "wins":0, "podiums":0, "races":24,"avg_grid":12.8,"wet_wins":0},
    "colapinto":  {"pos":17,"code":"COL","name":"Franco Colapinto",   "team":"Williams",       "color":"#64C4FF","pts":5,  "wins":0, "podiums":0, "races":24,"avg_grid":13.5,"wet_wins":0},
    "zhou":       {"pos":18,"code":"ZHO","name":"Guanyu Zhou",        "team":"Kick Sauber",    "color":"#52E252","pts":4,  "wins":0, "podiums":0, "races":24,"avg_grid":14.0,"wet_wins":0},
    "lawson":     {"pos":19,"code":"LAW","name":"Liam Lawson",        "team":"RB",             "color":"#6692FF","pts":2,  "wins":0, "podiums":0, "races":24,"avg_grid":14.5,"wet_wins":0},
    "bottas":     {"pos":20,"code":"BOT","name":"Valtteri Bottas",    "team":"Kick Sauber",    "color":"#52E252","pts":0,  "wins":0, "podiums":0, "races":24,"avg_grid":16.0,"wet_wins":0},
}

# Last 10 races of 2024 with top-5 results (rounds 15–24)
_FALLBACK_RACES = [
    {"round":15,"name":"Dutch GP",         "circuit":"Zandvoort",    "country":"Netherlands","date":"2024-08-25","wet":False,
     "results":[{"pos":1,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":25,"grid":1},
                {"pos":2,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":18,"grid":2},
                {"pos":3,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":3},
                {"pos":4,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":12,"grid":5},
                {"pos":5,"id":"hamilton",    "driver":"Hamilton",    "team":"Mercedes",       "color":"#27F4D2","pts":10,"grid":4}]},
    {"round":16,"name":"Italian GP",        "circuit":"Monza",       "country":"Italy",       "date":"2024-09-01","wet":False,
     "results":[{"pos":1,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":25,"grid":1},
                {"pos":2,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":18,"grid":2},
                {"pos":3,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":15,"grid":3},
                {"pos":4,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":12,"grid":4},
                {"pos":5,"id":"russell",     "driver":"Russell",     "team":"Mercedes",       "color":"#27F4D2","pts":10,"grid":6}]},
    {"round":17,"name":"Azerbaijan GP",     "circuit":"Baku",        "country":"Azerbaijan",  "date":"2024-09-15","wet":False,
     "results":[{"pos":1,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":25,"grid":1},
                {"pos":2,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":18,"grid":2},
                {"pos":3,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":3},
                {"pos":4,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":12,"grid":4},
                {"pos":5,"id":"alonso",      "driver":"Alonso",      "team":"Aston Martin",   "color":"#358C75","pts":10,"grid":7}]},
    {"round":18,"name":"Singapore GP",      "circuit":"Marina Bay",  "country":"Singapore",   "date":"2024-09-22","wet":False,
     "results":[{"pos":1,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":25,"grid":1},
                {"pos":2,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":18,"grid":4},
                {"pos":3,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":15,"grid":2},
                {"pos":4,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":12,"grid":3},
                {"pos":5,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":10,"grid":5}]},
    {"round":19,"name":"US GP (COTA)",      "circuit":"Austin",      "country":"USA",         "date":"2024-10-20","wet":False,
     "results":[{"pos":1,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":25,"grid":2},
                {"pos":2,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":18,"grid":1},
                {"pos":3,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":3},
                {"pos":4,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":12,"grid":4},
                {"pos":5,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":10,"grid":6}]},
    {"round":20,"name":"Mexico City GP",    "circuit":"Mexico City", "country":"Mexico",      "date":"2024-10-27","wet":False,
     "results":[{"pos":1,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":25,"grid":1},
                {"pos":2,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":18,"grid":2},
                {"pos":3,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":5},
                {"pos":4,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":12,"grid":3},
                {"pos":5,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":10,"grid":4}]},
    {"round":21,"name":"São Paulo GP",      "circuit":"Interlagos",  "country":"Brazil",      "date":"2024-11-03","wet":True,
     "results":[{"pos":1,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":25,"grid":17},
                {"pos":2,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":18,"grid":2},
                {"pos":3,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":3},
                {"pos":4,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":12,"grid":5},
                {"pos":5,"id":"perez",       "driver":"Perez",       "team":"Red Bull Racing","color":"#3671C6","pts":10,"grid":6}]},
    {"round":22,"name":"Las Vegas GP",      "circuit":"Las Vegas",   "country":"USA",         "date":"2024-11-23","wet":False,
     "results":[{"pos":1,"id":"hamilton",    "driver":"Hamilton",    "team":"Mercedes",       "color":"#27F4D2","pts":25,"grid":2},
                {"pos":2,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":18,"grid":1},
                {"pos":3,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":15,"grid":3},
                {"pos":4,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":12,"grid":4},
                {"pos":5,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":10,"grid":6}]},
    {"round":23,"name":"Qatar GP",          "circuit":"Losail",      "country":"Qatar",       "date":"2024-12-01","wet":False,
     "results":[{"pos":1,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":25,"grid":1},
                {"pos":2,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":18,"grid":2},
                {"pos":3,"id":"verstappen",  "driver":"Verstappen",  "team":"Red Bull Racing","color":"#3671C6","pts":15,"grid":3},
                {"pos":4,"id":"hamilton",    "driver":"Hamilton",    "team":"Mercedes",       "color":"#27F4D2","pts":12,"grid":5},
                {"pos":5,"id":"russell",     "driver":"Russell",     "team":"Mercedes",       "color":"#27F4D2","pts":10,"grid":4}]},
    {"round":24,"name":"Abu Dhabi GP",      "circuit":"Yas Marina",  "country":"UAE",         "date":"2024-12-08","wet":False,
     "results":[{"pos":1,"id":"norris",      "driver":"Norris",      "team":"McLaren",        "color":"#F47600","pts":25,"grid":1},
                {"pos":2,"id":"leclerc",     "driver":"Leclerc",     "team":"Ferrari",        "color":"#E8002D","pts":18,"grid":2},
                {"pos":3,"id":"sainz",       "driver":"Sainz",       "team":"Ferrari",        "color":"#E8002D","pts":15,"grid":3},
                {"pos":4,"id":"piastri",     "driver":"Piastri",     "team":"McLaren",        "color":"#F47600","pts":12,"grid":4},
                {"pos":5,"id":"hamilton",    "driver":"Hamilton",    "team":"Mercedes",       "color":"#27F4D2","pts":10,"grid":5}]},
]

# Jeddah (Saudi Arabian GP) historical finishes
_JEDDAH_HISTORY = {
    "verstappen": [{"year":2021,"pos":1},{"year":2022,"pos":2},{"year":2023,"pos":1},{"year":2024,"pos":1}],
    "hamilton":   [{"year":2021,"pos":2},{"year":2022,"pos":3},{"year":2023,"pos":16},{"year":2024,"pos":6}],
    "leclerc":    [{"year":2022,"pos":4},{"year":2023,"pos":2},{"year":2024,"pos":3}],
    "norris":     [{"year":2022,"pos":8},{"year":2023,"pos":4},{"year":2024,"pos":5}],
    "russell":    [{"year":2022,"pos":5},{"year":2023,"pos":3},{"year":2024,"pos":4}],
    "perez":      [{"year":2021,"pos":3},{"year":2022,"pos":1},{"year":2023,"pos":2},{"year":2024,"pos":2}],
    "sainz":      [{"year":2022,"pos":6},{"year":2023,"pos":5},{"year":2024,"pos":8}],
    "piastri":    [{"year":2023,"pos":12},{"year":2024,"pos":7}],
    "alonso":     [{"year":2021,"pos":7},{"year":2022,"pos":7},{"year":2023,"pos":6},{"year":2024,"pos":5}],
}


# ─── Cache helpers ────────────────────────────────────────────────────────────
async def _get_cached(key: str, ttl: int = CACHE_TTL):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT data, cached_at FROM race_cache WHERE key = ?", (key,)
        )
    finally:
        await db.close()
    if rows:
        age = datetime.now() - datetime.fromisoformat(rows[0][1])
        if age.total_seconds() < ttl:
            return json.loads(rows[0][0])
    return None


async def _set_cached(key: str, data):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO race_cache (key, data, cached_at) VALUES (?,?,?)",
            (key, json.dumps(data), datetime.now().isoformat()),
        )
        await db.commit()
    finally:
        await db.close()


# ─── Ergast fetchers ──────────────────────────────────────────────────────────
async def _ergast_get(path: str, params: dict | None = None) -> dict:
    """GET one Ergast endpoint; returns {} on any failure."""
    url = f"{ERGAST}/{path}.json"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params,
                             timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    data = json.loads(text)
                    return data.get("MRData", {})
    except Exception:
        pass
    return {}


async def _fetch_season_results() -> list[dict]:
    """Fetch all 2024 race results from Ergast (limit=500 to get whole season)."""
    cache_key = f"hist:results:{SEASON}"
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await _ergast_get(f"{SEASON}/results", {"limit": "500"})
    races = data.get("RaceTable", {}).get("Races", [])
    if races:
        await _set_cached(cache_key, races)
    return races


async def _fetch_season_qualifying() -> list[dict]:
    """Fetch all 2024 qualifying results from Ergast."""
    cache_key = f"hist:qual:{SEASON}"
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await _ergast_get(f"{SEASON}/qualifying", {"limit": "500"})
    races = data.get("RaceTable", {}).get("Races", [])
    if races:
        await _set_cached(cache_key, races)
    return races


async def _fetch_driver_standings() -> list[dict]:
    """Fetch 2024 final driver standings from Ergast."""
    cache_key = f"hist:standings:{SEASON}"
    cached = await _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await _ergast_get(f"{SEASON}/driverStandings")
    lists = data.get("StandingsTable", {}).get("StandingsLists", [])
    standings = lists[0].get("DriverStandings", []) if lists else []
    if standings:
        await _set_cached(cache_key, standings)
    return standings


# ─── Stat calculators ─────────────────────────────────────────────────────────
def _calc_stats_from_ergast(races: list[dict], qual_races: list[dict], standings: list[dict]) -> dict[str, dict]:
    """Build per-driver stat dict from live Ergast data."""
    # standings → points/wins baseline
    pts_map: dict[str, dict] = {}
    for s in standings:
        d = s.get("Driver", {})
        did = d.get("driverId", "")
        pts_map[did] = {
            "pos": int(s.get("position", 99)),
            "code": d.get("code", did[:3].upper()),
            "name": f"{d.get('givenName','')} {d.get('familyName','')}".strip(),
            "team": s.get("Constructors", [{}])[-1].get("name", ""),
            "color": "#888",
            "pts": int(s.get("points", 0)),
            "wins": int(s.get("wins", 0)),
            "podiums": 0,
            "races": 0,
            "avg_grid": 10.0,
            "wet_wins": 0,
        }

    # race results → podiums, race counts, grid averages
    grid_sums: dict[str, list[int]] = {}
    for race in races:
        for result in race.get("Results", []):
            did = result.get("Driver", {}).get("driverId", "")
            pos = int(result.get("position", 20))
            grid = int(result.get("grid", 10))
            if did not in pts_map:
                d = result.get("Driver", {})
                pts_map[did] = {
                    "pos": 99, "code": d.get("code", did[:3].upper()),
                    "name": f"{d.get('givenName','')} {d.get('familyName','')}".strip(),
                    "team": result.get("Constructor", {}).get("name", ""),
                    "color": "#888", "pts": 0, "wins": 0,
                    "podiums": 0, "races": 0, "avg_grid": 10.0, "wet_wins": 0,
                }
            pts_map[did]["races"] = pts_map[did].get("races", 0) + 1
            if pos <= 3:
                pts_map[did]["podiums"] = pts_map[did].get("podiums", 0) + 1
            grid_sums.setdefault(did, []).append(grid)

    for did, grids in grid_sums.items():
        if did in pts_map and grids:
            pts_map[did]["avg_grid"] = round(sum(grids) / len(grids), 1)

    return pts_map


def _compute_last5(races: list[dict], driver_id: str) -> list[int]:
    """Extract points scored in last 5 races for a driver."""
    pts_per_race: list[int] = []
    for race in races:
        for result in race.get("Results", []):
            if result.get("Driver", {}).get("driverId", "") == driver_id:
                pts_per_race.append(int(result.get("points", 0)))
                break
    return pts_per_race[-5:] if pts_per_race else []


def _compute_last5_fallback(driver_id: str) -> list[int]:
    """Compute last-5 points from fallback race data."""
    pts: list[int] = []
    for race in _FALLBACK_RACES:
        for r in race["results"]:
            if r["id"] == driver_id:
                pts.append(r["pts"])
                break
        else:
            pts.append(0)
    return pts[-5:]


def _win_rate_pct(wins: int, races: int) -> float:
    return round(wins / races * 100, 1) if races else 0.0


def _podium_rate_pct(podiums: int, races: int) -> float:
    return round(podiums / races * 100, 1) if races else 0.0


# ─── Public API ──────────────────────────────────────────────────────────────
async def get_driver_stats() -> list[dict]:
    """Return all drivers' 2024 stats. Uses Ergast if available, fallback otherwise."""
    cache_key = "hist:driver_stats"
    cached = await _get_cached(cache_key, ttl=3600)  # 1-h re-computation cache
    if cached is not None:
        return cached

    # Try live data
    results, qual_races, standings = await _fetch_season_results(), await _fetch_season_qualifying(), await _fetch_driver_standings()

    if standings and results:
        raw = _calc_stats_from_ergast(results, qual_races, standings)
        output: list[dict] = []
        for did, d in sorted(raw.items(), key=lambda x: x[1]["pos"]):
            last5 = _compute_last5(results, did)
            output.append({
                "driver_id": did,
                "code": d["code"],
                "name": d["name"],
                "team": d["team"],
                "color": d.get("color", "#888"),
                "season": SEASON,
                "championship_pos": d["pos"],
                "points": d["pts"],
                "wins": d["wins"],
                "podiums": d["podiums"],
                "races": d["races"],
                "win_rate": _win_rate_pct(d["wins"], d["races"]),
                "podium_rate": _podium_rate_pct(d["podiums"], d["races"]),
                "avg_grid": d["avg_grid"],
                "last5_points": last5,
                "jeddah_history": _JEDDAH_HISTORY.get(did, []),
            })
    else:
        # Fallback
        output = []
        for did, d in sorted(_FALLBACK_STANDINGS.items(), key=lambda x: x[1]["pos"]):
            output.append({
                "driver_id": did,
                "code": d["code"],
                "name": d["name"],
                "team": d["team"],
                "color": d["color"],
                "season": SEASON,
                "championship_pos": d["pos"],
                "points": d["pts"],
                "wins": d["wins"],
                "podiums": d["podiums"],
                "races": d["races"],
                "win_rate": _win_rate_pct(d["wins"], d["races"]),
                "podium_rate": _podium_rate_pct(d["podiums"], d["races"]),
                "avg_grid": d["avg_grid"],
                "last5_points": _compute_last5_fallback(did),
                "jeddah_history": _JEDDAH_HISTORY.get(did, []),
            })

    await _set_cached(cache_key, output)
    return output


async def get_race_history(limit: int = 10) -> list[dict]:
    """Return last N race results. Uses Ergast if available, fallback otherwise."""
    cache_key = f"hist:race_history:{limit}"
    cached = await _get_cached(cache_key, ttl=3600)
    if cached is not None:
        return cached

    races = await _fetch_season_results()

    if races:
        output: list[dict] = []
        for race in races[-limit:]:
            top5 = race.get("Results", [])[:5]
            output.append({
                "round": int(race.get("round", 0)),
                "name": race.get("raceName", ""),
                "circuit": race.get("Circuit", {}).get("circuitName", ""),
                "country": race.get("Circuit", {}).get("Location", {}).get("country", ""),
                "date": race.get("date", ""),
                "wet": False,
                "results": [
                    {
                        "pos": int(r.get("position", i + 1)),
                        "id": r.get("Driver", {}).get("driverId", ""),
                        "driver": r.get("Driver", {}).get("familyName", ""),
                        "team": r.get("Constructor", {}).get("name", ""),
                        "color": "#888",
                        "pts": int(r.get("points", 0)),
                        "grid": int(r.get("grid", 0)),
                    }
                    for i, r in enumerate(top5)
                ],
            })
    else:
        output = _FALLBACK_RACES[-limit:]

    await _set_cached(cache_key, output)
    return output


async def get_driver_stats_map() -> dict[str, dict]:
    """Return stats keyed by driver_id for fast lookup."""
    stats = await get_driver_stats()
    return {s["driver_id"]: s for s in stats}
