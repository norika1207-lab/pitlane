"""進站效率分析 — 從 OpenF1 /pit 端點拉取"""
from services import openf1


async def get_team_pit_stats(session_key: int) -> dict:
    """分析各車隊進站效率"""
    pit_data = await openf1.get_pit_stops(session_key)
    if not pit_data:
        return {}

    team_stats = {}
    for stop in pit_data:
        team = stop.get("team_name")
        duration = stop.get("pit_duration")
        if not team or not duration:
            continue

        if team not in team_stats:
            team_stats[team] = {"stops": [], "fastest": 999, "error_count": 0}

        team_stats[team]["stops"].append(duration)
        if duration < team_stats[team]["fastest"]:
            team_stats[team]["fastest"] = duration
        if duration > 5.0:
            team_stats[team]["error_count"] += 1

    for team in team_stats:
        stops = team_stats[team]["stops"]
        avg = round(sum(stops) / len(stops), 2) if stops else 0
        error_rate = round(team_stats[team]["error_count"] / len(stops) * 100, 1) if stops else 0
        reliability = max(0, min(100, int(100 - error_rate * 5 - max(0, avg - 2.5) * 10)))
        team_stats[team].update({
            "average": avg,
            "total_stops": len(stops),
            "error_rate": error_rate,
            "reliability": reliability,
        })
        del team_stats[team]["stops"]

    return team_stats
