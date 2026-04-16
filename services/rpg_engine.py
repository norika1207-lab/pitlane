"""PitLane RPG 引擎 — 等級/XP/稱號/外框/獎杯/血型"""
import math
from datetime import datetime

# ════════════════════════════════════════════
# 等級系統（100 級，每級需要更多 XP）
# ════════════════════════════════════════════
LEVEL_TIERS = [
    (1, 5, "新手分析師", "ROOKIE", "基本下注、看公開數據"),
    (6, 10, "賽車觀察員", "OBSERVER", "中階下注、看進站數據"),
    (11, 20, "策略研究員", "ANALYST", "進階下注、看聰明錢流向"),
    (21, 35, "資深分析師", "SR_ANALYST", "P2P 開單、看重壓分布"),
    (36, 50, "技術總監", "TD", "開挑戰房間、看 VIP 數據報告"),
    (51, 70, "車隊經理", "GM", "自設賠率、看全站押注分布"),
    (71, 85, "賽事總監", "DIRECTOR", "專屬外框、限定卡面、稱號客製"),
    (86, 95, "傳奇分析師", "LEGEND", "每站分析報告提前 24 小時看"),
    (96, 99, "車隊老闆", "OWNER", "全站最高權限、限定獎杯展示"),
    (100, 100, "F1 教父", "GODFATHER", "唯一稱號、專屬金色外框、永久榮耀"),
]

FRAMES = {
    "silverstone": {"name": "銀石框", "min_level": 1, "css": "border:2px solid #666"},
    "monza": {"name": "蒙扎框", "min_level": 10, "css": "border:2px solid;border-image:linear-gradient(135deg,#00b0ff,#a855f7) 1"},
    "suzuka": {"name": "鈴鹿框", "min_level": 25, "css": "border:2px solid #a855f7;box-shadow:0 0 8px rgba(168,85,247,0.3)"},
    "monaco": {"name": "摩納哥框", "min_level": 50, "css": "border:2px solid #e8ff00;box-shadow:0 0 12px rgba(232,255,0,0.3)"},
    "champion": {"name": "冠軍框", "min_level": 0, "special": "annual_rank_1", "css": "border:2px solid;border-image:linear-gradient(90deg,#ff0,#0ff,#f0f,#ff0) 1;animation:rainbowBorder 3s linear infinite"},
    "legend": {"name": "傳奇框", "min_level": 100, "css": "border:3px solid #e8ff00;box-shadow:0 0 20px rgba(232,255,0,0.4),inset 0 0 10px rgba(232,255,0,0.1)"},
}


def xp_for_level(level: int) -> int:
    """XP needed to reach a given level."""
    if level <= 1:
        return 0
    return int(100 * (level ** 1.5))


def level_from_xp(total_xp: int) -> dict:
    """Calculate level, progress, and tier from total XP."""
    level = 1
    while xp_for_level(level + 1) <= total_xp and level < 100:
        level += 1

    current_level_xp = xp_for_level(level)
    next_level_xp = xp_for_level(level + 1) if level < 100 else current_level_xp
    progress_xp = total_xp - current_level_xp
    needed_xp = next_level_xp - current_level_xp

    # Find tier
    title = "新手分析師"
    code = "ROOKIE"
    perks = ""
    for min_l, max_l, t, c, p in LEVEL_TIERS:
        if min_l <= level <= max_l:
            title = t
            code = c
            perks = p
            break

    # Available frames
    available_frames = [k for k, v in FRAMES.items() if v["min_level"] <= level and "special" not in v]

    return {
        "level": level,
        "total_xp": total_xp,
        "xp_in_level": progress_xp,
        "xp_to_next": needed_xp,
        "progress_pct": round(progress_xp / max(needed_xp, 1) * 100, 1),
        "title": title,
        "title_code": code,
        "perks": perks,
        "available_frames": available_frames,
        "is_max": level >= 100,
    }


# ════════════════════════════════════════════
# XP 獲得規則
# ════════════════════════════════════════════
XP_RULES = {
    "bet_placed": 10,
    "bet_won_champion": 100,
    "bet_won_podium": 50,
    "bet_won_dark_horse": 200,  # odds >= 10x
    "bet_perfect": 500,  # all correct
    "p2p_created": 20,
    "p2p_accepted": 30,
    "challenge_won": 150,
    "challenge_lost": -30,
    "follower_won": 80,  # someone followed you and won
    "followed_won": 50,  # you followed someone and won
}

STREAK_MULTIPLIERS = {
    3: 1.5,
    5: 2.0,
    10: 3.0,
}


def calculate_xp_reward(action: str, streak: int = 0, odds: float = 1.0) -> int:
    """Calculate XP for an action with streak multiplier."""
    base = XP_RULES.get(action, 0)
    if base == 0:
        return 0

    multiplier = 1.0
    # Streak bonus
    for threshold, mult in sorted(STREAK_MULTIPLIERS.items(), reverse=True):
        if streak >= threshold:
            multiplier = mult
            break

    # Dark horse bonus
    if action == "bet_won_champion" and odds >= 10.0:
        base = XP_RULES["bet_won_dark_horse"]
        multiplier *= 3.0

    return int(base * multiplier)


# ════════════════════════════════════════════
# 稱號系統
# ════════════════════════════════════════════
AUTO_TITLES = {
    "rain_prophet": {"name": "雨神追隨者", "condition": "雨戰預測準度 80%+", "icon": "🌧"},
    "pit_master": {"name": "進站大師", "condition": "進站策略預測準度 75%+", "icon": "🔧"},
    "dark_hunter": {"name": "黑馬獵人", "condition": "押中賠率 15x+ 超過 5 次", "icon": "🎯"},
    "streak_machine": {"name": "連勝機器", "condition": "連續 10 站預測正確", "icon": "🔥"},
    "ferrari_believer": {"name": "Ferrari 信徒", "condition": "押 Ferrari 車手超過 50 次", "icon": "🔴"},
    "mclaren_army": {"name": "McLaren 橘色軍團", "condition": "押 McLaren 連勝 5 次", "icon": "🧡"},
    "redbull_wing": {"name": "Red Bull 能量使者", "condition": "押 Red Bull 車手超過 50 次", "icon": "🐂"},
    "mercedes_silver": {"name": "Mercedes 銀箭粉", "condition": "押 Mercedes 車手超過 30 次", "icon": "⚡"},
    "safety_car_guru": {"name": "安全車預言家", "condition": "安全車預測準度 85%+", "icon": "🚗"},
    "consistent_king": {"name": "穩定之王", "condition": "連續 20 站都有下注", "icon": "👑"},
}


def check_auto_titles(user_stats: dict) -> list:
    """Check which auto-titles a user has earned."""
    earned = []
    total = user_stats.get("total_bets", 0)
    wins = user_stats.get("total_wins", 0)
    streak = user_stats.get("win_streak", 0)
    dark_horse_wins = user_stats.get("dark_horse_wins", 0)

    if total >= 10 and wins / max(total, 1) >= 0.8:
        earned.append("rain_prophet")
    if dark_horse_wins >= 5:
        earned.append("dark_hunter")
    if streak >= 10:
        earned.append("streak_machine")
    if total >= 20:
        earned.append("consistent_king")

    return [{"id": t, **AUTO_TITLES[t]} for t in earned]


# ════════════════════════════════════════════
# 獎杯系統
# ════════════════════════════════════════════
TROPHY_TYPES = {
    "bronze": {"name": "銅牌獎杯", "icon": "🥉", "condition": "押中前三名"},
    "silver": {"name": "銀牌獎杯", "icon": "🥈", "condition": "押中冠軍"},
    "gold": {"name": "金牌獎杯", "icon": "🥇", "condition": "完全命中"},
    "legendary": {"name": "傳奇獎杯", "icon": "🏆", "condition": "押中賠率 20x+ 冠軍"},
    "season": {"name": "賽季獎杯", "icon": "🏅", "condition": "整季預測準度第一"},
}


# ════════════════════════════════════════════
# 賽車血型分析
# ════════════════════════════════════════════
def analyze_racing_blood_type(team_bets: dict) -> dict:
    """Analyze user's racing personality from betting history."""
    total = sum(team_bets.values())
    if total == 0:
        return {"type": "新秀", "desc": "還沒有足夠的數據分析你的賽車血型", "icon": "🌱"}

    # Calculate percentages
    pcts = {k: v / total * 100 for k, v in team_bets.items()}
    top_team = max(pcts, key=pcts.get) if pcts else ""
    top_pct = pcts.get(top_team, 0)

    # Determine blood type
    speed_teams = {"Red Bull Racing", "McLaren", "Ferrari"}
    strategy_teams = {"Mercedes", "Aston Martin", "Alpine"}
    underdog_teams = {"Williams", "Haas", "Racing Bulls", "Audi"}

    speed_pct = sum(pcts.get(t, 0) for t in speed_teams)
    strategy_pct = sum(pcts.get(t, 0) for t in strategy_teams)
    underdog_pct = sum(pcts.get(t, 0) for t in underdog_teams)

    if underdog_pct >= 40:
        blood = {"type": "黑馬獵人", "desc": "你喜歡押冷門，追求高賠率高報酬。膽子大，眼光獨到。", "icon": "🎯"}
    elif speed_pct >= 60:
        blood = {"type": "速度狂", "desc": "你偏愛強隊強將，追求穩定勝率。務實派分析師。", "icon": "🏎"}
    elif strategy_pct >= 40:
        blood = {"type": "策略師", "desc": "你重視進站策略和車隊執行力。思考型玩家。", "icon": "🧠"}
    elif top_pct >= 50:
        blood = {"type": f"{top_team} 死忠", "desc": f"你超過一半的押注都給了 {top_team}。忠誠度滿分。", "icon": "❤️"}
    else:
        blood = {"type": "全面分析師", "desc": "你不偏袒任何車隊，每次都根據數據判斷。理性派代表。", "icon": "📊"}

    blood["team_distribution"] = {k: round(v, 1) for k, v in sorted(pcts.items(), key=lambda x: -x[1])[:5]}
    return blood


# ════════════════════════════════════════════
# 在線狀態
# ════════════════════════════════════════════
STATUS_TYPES = {
    "online": {"label": "在線", "color": "#00ff88", "can_challenge": True},
    "racing": {"label": "比賽中", "color": "#e8ff00", "can_challenge": False},
    "analyzing": {"label": "分析中", "color": "#a855f7", "can_challenge": False},
    "offline": {"label": "離線", "color": "#ff4444", "can_challenge": False},
    "top10": {"label": "排行前10", "color": "#e8ff00", "can_challenge": True},
}
