"""賠率計算引擎 — 綜合歷史+近況+賽道+天氣"""
from services.card_engine import DRIVER_BASE_STATS
from services.track_data import get_track
from services.race_names import get_circuit_type_raw
from config import FEE_CONFIG


def calculate_winner_odds(driver_id: str, circuit: str = "", weather: dict = None) -> float:
    """綜合勝率計算 → 賠率"""
    key = driver_id.lower()[:3]
    base = DRIVER_BASE_STATS.get(key, {})
    if not base:
        return 25.0

    overall = (base.get("q", 50) + base.get("t", 50) + base.get("w", 50) +
               base.get("o", 50) + base.get("s", 50)) / 5

    # Track type bonus
    track = get_track(circuit)
    ct = track.get("type", "technical")
    if ct == "street":
        overall = overall * 0.6 + base.get("s", 50) * 0.4
    elif ct == "high_speed":
        overall = overall * 0.6 + base.get("q", 50) * 0.4

    # Weather adjustment
    if weather and weather.get("rainfall", 0) > 0:
        overall = overall * 0.5 + base.get("w", 50) * 0.5

    # Convert to probability then odds
    prob = max(0.01, min(0.7, (overall / 100) * 0.75))
    odds = round(1 / prob, 1)
    return max(1.05, min(100.0, odds))


def calculate_h2h_odds(driver_a: str, driver_b: str) -> tuple:
    """H2H 對決賠率"""
    ka = driver_a.lower()[:3]
    kb = driver_b.lower()[:3]
    ba = DRIVER_BASE_STATS.get(ka, {})
    bb = DRIVER_BASE_STATS.get(kb, {})
    oa = sum(ba.values()) / max(len(ba), 1) if ba else 50
    ob = sum(bb.values()) / max(len(bb), 1) if bb else 50
    total = oa + ob
    pa = oa / total
    pb = ob / total
    return (round(1 / pa, 2), round(1 / pb, 2))


def calculate_podium_odds(driver_id: str, circuit: str = "") -> float:
    """前三名賠率（比冠軍低）"""
    winner_odds = calculate_winner_odds(driver_id, circuit)
    podium_odds = max(1.05, round(winner_odds * 0.4, 1))
    return podium_odds


def apply_fee(amount: float, fee_type: str = "system_bet") -> dict:
    """計算手續費"""
    rate = FEE_CONFIG.get(fee_type, 0.05)
    fee = round(amount * rate, 2)
    return {"amount": amount, "fee": fee, "total": round(amount + fee, 2), "rate": rate}


def get_market_odds(drivers: list, circuit: str = "") -> list:
    """生成全場賠率表"""
    result = []
    for d in drivers:
        did = d.get("driver_id", "")
        odds = calculate_winner_odds(did, circuit)
        podium = calculate_podium_odds(did, circuit)
        prob = round(1 / odds * 100, 1)
        result.append({
            "driver_id": did,
            "name": d.get("name", did),
            "team": d.get("team", ""),
            "winner_odds": odds,
            "podium_odds": podium,
            "win_probability": prob,
        })
    result.sort(key=lambda x: x["winner_odds"])
    return result
