"""Pit stop analysis — joins OpenF1 /pit with /drivers to get team breakdown."""
from services import openf1


async def get_team_pit_stats(session_key: int) -> dict:
    """Per-team pit stop statistics.

    Joins /pit (driver_number + stop_duration) with /drivers (driver_number -> team_name).
    Uses stop_duration (actual tyre-change time, ~2-4s) not pit_duration (lap time).
    """
    pit_rows = await openf1.get_pit_stops(session_key)
    drivers  = await openf1.get_drivers(session_key)
    if not pit_rows:
        return {}

    driver_to_team = {}
    driver_to_name = {}
    for d in drivers or []:
        num = d.get("driver_number")
        if num is None:
            continue
        driver_to_team[num] = d.get("team_name") or "Unknown"
        driver_to_name[num] = d.get("full_name") or d.get("broadcast_name") or f"#{num}"

    team_stats: dict[str, dict] = {}
    for row in pit_rows:
        dur = row.get("stop_duration") or row.get("pit_duration")
        if dur is None:
            continue
        team = driver_to_team.get(row.get("driver_number"), "Unknown")
        if team == "Unknown":
            continue

        bucket = team_stats.setdefault(team, {"durations": [], "drivers": {}, "errors": 0})
        bucket["durations"].append(float(dur))
        d_num = row.get("driver_number")
        d_bucket = bucket["drivers"].setdefault(d_num, {
            "name": driver_to_name.get(d_num, f"#{d_num}"),
            "stops": [],
        })
        d_bucket["stops"].append(float(dur))
        # "Error" threshold: >4s for stop_duration (tyre change), >30s for pit_duration
        error_threshold = 4.0 if row.get("stop_duration") is not None else 30.0
        if float(dur) > error_threshold:
            bucket["errors"] += 1

    # Compute aggregates
    result: dict[str, dict] = {}
    for team, b in team_stats.items():
        stops = b["durations"]
        if not stops:
            continue
        avg = round(sum(stops) / len(stops), 2)
        fastest = round(min(stops), 2)
        error_rate = round(b["errors"] / len(stops) * 100, 1)
        # Reliability score: 100 is perfect, subtract for slow avg + error rate
        reliability = max(0, min(100, int(100 - error_rate * 2 - max(0, avg - 2.5) * 15)))

        per_driver = [
            {
                "driver_number": num,
                "name": dd["name"],
                "stops": len(dd["stops"]),
                "fastest": round(min(dd["stops"]), 2),
                "average": round(sum(dd["stops"]) / len(dd["stops"]), 2),
            }
            for num, dd in b["drivers"].items()
        ]

        result[team] = {
            "average": avg,
            "fastest": fastest,
            "total_stops": len(stops),
            "error_count": b["errors"],
            "error_rate": error_rate,
            "reliability": reliability,
            "drivers": sorted(per_driver, key=lambda d: d["fastest"]),
        }

    # Sort teams by fastest single stop (fan-friendly ranking)
    return dict(sorted(result.items(), key=lambda kv: kv[1]["fastest"]))


async def get_session_pit_leaderboard(session_key: int, limit: int = 10) -> list[dict]:
    """Fastest individual pit stops of the session (for highlight UI)."""
    pit_rows = await openf1.get_pit_stops(session_key)
    drivers  = await openf1.get_drivers(session_key)
    if not pit_rows:
        return []

    d_map = {}
    for d in drivers or []:
        num = d.get("driver_number")
        if num is not None:
            d_map[num] = {
                "name": d.get("full_name") or d.get("broadcast_name") or f"#{num}",
                "team": d.get("team_name") or "Unknown",
                "color": d.get("team_colour"),
            }

    entries = []
    for r in pit_rows:
        dur = r.get("stop_duration")
        if dur is None:
            continue
        info = d_map.get(r.get("driver_number"), {})
        entries.append({
            "driver_number": r.get("driver_number"),
            "driver": info.get("name", "—"),
            "team": info.get("team", "—"),
            "color": ("#" + info["color"]) if info.get("color") else "#888",
            "lap": r.get("lap_number"),
            "duration": round(float(dur), 2),
        })

    entries.sort(key=lambda e: e["duration"])
    return entries[:limit]
