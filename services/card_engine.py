"""卡牌數值計算引擎 — 從歷史數據算出車手/車隊卡牌能力值
   若 Ergast 無歷史數據，使用基於車手名氣/車隊的合理預設值"""
import hashlib
from services import ergast


# Known top drivers with reasonable base stats (2024 season reference)
DRIVER_BASE_STATS = {
    "ver": {"q": 95, "t": 88, "w": 92, "o": 85, "s": 80},  # Verstappen
    "nor": {"q": 90, "t": 85, "w": 78, "o": 88, "s": 82},  # Norris
    "lec": {"q": 92, "t": 80, "w": 75, "o": 78, "s": 90},  # Leclerc
    "sai": {"q": 85, "t": 82, "w": 72, "o": 75, "s": 85},  # Sainz
    "ham": {"q": 88, "t": 90, "w": 95, "o": 82, "s": 88},  # Hamilton
    "rus": {"q": 87, "t": 78, "w": 80, "o": 76, "s": 75},  # Russell
    "pia": {"q": 82, "t": 75, "w": 65, "o": 80, "s": 70},  # Piastri
    "alo": {"q": 80, "t": 92, "w": 88, "o": 78, "s": 85},  # Alonso
    "gas": {"q": 78, "t": 76, "w": 72, "o": 74, "s": 78},  # Gasly
    "oco": {"q": 75, "t": 74, "w": 70, "o": 72, "s": 73},  # Ocon
    "str": {"q": 76, "t": 73, "w": 68, "o": 76, "s": 72},  # Stroll
    "tsu": {"q": 77, "t": 72, "w": 66, "o": 73, "s": 70},  # Tsunoda
    "hul": {"q": 74, "t": 78, "w": 74, "o": 70, "s": 72},  # Hulkenberg
    "mag": {"q": 72, "t": 70, "w": 68, "o": 72, "s": 70},  # Magnussen
    "per": {"q": 78, "t": 75, "w": 72, "o": 68, "s": 80},  # Perez
    "bot": {"q": 76, "t": 80, "w": 70, "o": 65, "s": 70},  # Bottas
    "zho": {"q": 68, "t": 70, "w": 62, "o": 65, "s": 65},  # Zhou
    "alb": {"q": 74, "t": 76, "w": 68, "o": 72, "s": 70},  # Albon
    "sar": {"q": 65, "t": 65, "w": 58, "o": 62, "s": 60},  # Sargeant
    "ric": {"q": 80, "t": 75, "w": 78, "o": 82, "s": 78},  # Ricciardo
    "law": {"q": 72, "t": 68, "w": 60, "o": 70, "s": 65},  # Lawson
    "bor": {"q": 70, "t": 68, "w": 60, "o": 68, "s": 62},  # Bortoleto
    "had": {"q": 68, "t": 65, "w": 58, "o": 66, "s": 60},  # Hadjar
    "doo": {"q": 72, "t": 70, "w": 62, "o": 70, "s": 65},  # Doohan
    "ant": {"q": 70, "t": 66, "w": 58, "o": 68, "s": 62},  # Antonelli
    "bea": {"q": 78, "t": 74, "w": 70, "o": 75, "s": 72},  # Bearman
}

TEAM_RANKINGS = {
    "mclaren": 1, "red_bull_racing": 2, "ferrari": 3, "mercedes": 4,
    "aston_martin": 5, "alpine": 6, "williams": 7, "haas": 8,
    "rb": 9, "audi": 10, "racing_bulls": 9, "kick_sauber": 10,
}


def _hash_seed(driver_id: str) -> int:
    """Generate a deterministic seed from driver ID."""
    return int(hashlib.md5(driver_id.encode()).hexdigest()[:8], 16)


async def calculate_driver_card(driver_id: str, year: int = 2024) -> dict:
    """Calculate driver card stats. Use known base stats or generate from Ergast."""
    acronym = driver_id.lower()[:3]

    # Check if we have base stats for this driver
    base = DRIVER_BASE_STATS.get(acronym)
    if base:
        qualifying = base["q"]
        tire_management = base["t"]
        wet_weather = base["w"]
        overtaking = base["o"]
        street_circuit = base["s"]
    else:
        # Try Ergast historical data
        results = await ergast.get_driver_results(driver_id, year)
        if results:
            return _calc_from_results(results, year, driver_id)

        # Generate reasonable random-ish stats based on driver_id hash
        seed = _hash_seed(driver_id)
        qualifying = 55 + (seed % 35)
        tire_management = 55 + ((seed >> 4) % 30)
        wet_weather = 50 + ((seed >> 8) % 35)
        overtaking = 55 + ((seed >> 12) % 30)
        street_circuit = 50 + ((seed >> 16) % 35)

    overall = int((qualifying + tire_management + wet_weather + overtaking + street_circuit) / 5)

    return {
        "qualifying": qualifying,
        "tire_management": tire_management,
        "wet_weather": wet_weather,
        "overtaking": overtaking,
        "street_circuit": street_circuit,
        "overall": overall,
        "season_points": 0,
        "wins": 0,
        "podiums": 0,
        "races": 0,
    }


def _calc_from_results(results, year, driver_id):
    """Calculate stats from actual Ergast race results."""
    total_races = len(results)
    wins = 0
    podiums = 0
    grid_positions = []
    position_gains = []

    for race in results:
        for result in race.get("Results", []):
            pos = int(result.get("position", 20))
            grid = int(result.get("grid", 20))
            grid_positions.append(grid)
            position_gains.append(grid - pos)
            if pos == 1: wins += 1
            if pos <= 3: podiums += 1

    avg_grid = sum(grid_positions) / len(grid_positions) if grid_positions else 15
    qualifying = max(0, min(100, int(100 - (avg_grid - 1) * 5)))
    avg_gain = sum(position_gains) / len(position_gains) if position_gains else 0
    overtaking = max(0, min(100, int(50 + avg_gain * 10)))
    podium_rate = podiums / total_races if total_races > 0 else 0
    tire_management = max(0, min(100, int(podium_rate * 100 + 20)))
    win_rate = wins / total_races if total_races > 0 else 0
    wet_weather = max(0, min(100, int(win_rate * 150 + 30)))
    street_circuit = max(0, min(100, int(win_rate * 120 + 25)))
    overall = int((qualifying + tire_management + wet_weather + overtaking + street_circuit) / 5)

    return {
        "qualifying": qualifying,
        "tire_management": tire_management,
        "wet_weather": wet_weather,
        "overtaking": overtaking,
        "street_circuit": street_circuit,
        "overall": overall,
        "season_points": 0,
        "wins": wins,
        "podiums": podiums,
        "races": total_races,
    }


async def calculate_constructor_card(constructor_id: str, year: int = 2024) -> dict:
    """Calculate constructor card stats."""
    # Normalize constructor ID
    cid = constructor_id.lower().replace(" ", "_")

    ranking = TEAM_RANKINGS.get(cid, 6)

    car_speed = max(0, min(100, int(100 - (ranking - 1) * 8)))
    pit_efficiency = max(0, min(100, int(90 - (ranking - 1) * 5)))
    strategy = max(0, min(100, int(88 - (ranking - 1) * 6)))
    track_adaptability = max(0, min(100, int(85 - (ranking - 1) * 5)))

    return {
        "car_speed": car_speed,
        "pit_efficiency": pit_efficiency,
        "strategy": strategy,
        "track_adaptability": track_adaptability,
        "overall": int((car_speed + pit_efficiency + strategy + track_adaptability) / 4),
        "season_points": 0,
        "championship_position": ranking,
    }


def calculate_odds(driver_stats: dict, total_drivers: int = 20) -> float:
    """Calculate betting odds for a driver."""
    overall = driver_stats.get("overall", 50)
    base_prob = overall / 100
    win_prob = max(0.02, min(0.6, base_prob * 0.7))
    odds = round(1 / win_prob, 1)
    return max(1.1, min(50.0, odds))


def determine_rarity(user) -> str:
    """Determine what rarity cards a user can access."""
    total_bets = user.get("total_bets", 0) if isinstance(user, dict) else getattr(user, "total_bets", 0)
    total_wins = user.get("total_wins", 0) if isinstance(user, dict) else getattr(user, "total_wins", 0)
    win_rate = total_wins / total_bets if total_bets > 0 else 0

    if total_bets >= 50 and win_rate >= 0.8:
        return "monaco"
    elif total_bets >= 20 and win_rate >= 0.6:
        return "suzuka"
    elif total_bets >= 10:
        return "monza"
    return "silverstone"
