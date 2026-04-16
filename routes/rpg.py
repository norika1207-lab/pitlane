"""RPG 系統 API — 等級/XP/稱號/獎杯/血型"""
from fastapi import APIRouter, Header, HTTPException
from database import get_db
from routes.auth import get_current_user
from services.rpg_engine import (
    level_from_xp, calculate_xp_reward, check_auto_titles,
    analyze_racing_blood_type, TROPHY_TYPES, FRAMES, AUTO_TITLES, STATUS_TYPES,
)

router = APIRouter(prefix="/api/rpg", tags=["rpg"])


async def _get_user_rpg(username: str) -> dict:
    """Get or create user RPG data."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT xp, win_streak, dark_horse_wins, frame, custom_title, status FROM user_rpg WHERE username = ?",
            (username,),
        )
        if rows:
            return {
                "xp": rows[0][0], "win_streak": rows[0][1],
                "dark_horse_wins": rows[0][2], "frame": rows[0][3],
                "custom_title": rows[0][4], "status": rows[0][5],
            }
        # Create default
        await db.execute(
            "INSERT INTO user_rpg (username, xp, win_streak, dark_horse_wins, frame, status) VALUES (?, 0, 0, 0, 'silverstone', 'online')",
            (username,),
        )
        await db.commit()
        return {"xp": 0, "win_streak": 0, "dark_horse_wins": 0, "frame": "silverstone", "custom_title": None, "status": "online"}
    finally:
        await db.close()


async def _add_xp(username: str, amount: int, reason: str):
    """Add XP and log it."""
    db = await get_db()
    try:
        await db.execute("UPDATE user_rpg SET xp = xp + ? WHERE username = ?", (amount, username))
        await db.execute(
            "INSERT INTO xp_log (username, amount, reason, created_at) VALUES (?, ?, ?, datetime('now'))",
            (username, amount, reason),
        )
        await db.commit()
    finally:
        await db.close()


@router.get("/profile")
async def rpg_profile(authorization: str = Header(None)):
    """Complete RPG profile."""
    user = await get_current_user(authorization)
    username = user["username"]
    rpg = await _get_user_rpg(username)
    level_info = level_from_xp(rpg["xp"])

    # Get bet stats
    db = await get_db()
    try:
        bet_stats = await db.execute_fetchall(
            """SELECT COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END)
               FROM bets WHERE username = ?""",
            (username,),
        )
        total_bets = bet_stats[0][0] if bet_stats else 0
        total_wins = bet_stats[0][1] or 0 if bet_stats else 0

        # Trophies
        trophies = await db.execute_fetchall(
            "SELECT trophy_type, race_name, driver, created_at FROM trophies WHERE username = ? ORDER BY created_at DESC LIMIT 20",
            (username,),
        )
        trophy_list = [{"type": t[0], "race": t[1], "driver": t[2], "date": t[3],
                        **TROPHY_TYPES.get(t[0], {})} for t in trophies]

        # XP history
        xp_history = await db.execute_fetchall(
            "SELECT amount, reason, created_at FROM xp_log WHERE username = ? ORDER BY created_at DESC LIMIT 10",
            (username,),
        )
    finally:
        await db.close()

    # Auto titles
    user_stats = {
        "total_bets": total_bets, "total_wins": total_wins,
        "win_streak": rpg["win_streak"], "dark_horse_wins": rpg["dark_horse_wins"],
    }
    titles = check_auto_titles(user_stats)

    # Blood type (simplified - would need team bet breakdown)
    blood_type = analyze_racing_blood_type({})

    frame_info = FRAMES.get(rpg["frame"], FRAMES["silverstone"])

    return {
        "username": username,
        "level": level_info,
        "frame": {"id": rpg["frame"], **frame_info},
        "status": rpg["status"],
        "status_info": STATUS_TYPES.get(rpg["status"], STATUS_TYPES["online"]),
        "custom_title": rpg["custom_title"],
        "auto_titles": titles,
        "trophies": trophy_list,
        "trophy_count": len(trophy_list),
        "blood_type": blood_type,
        "stats": {"total_bets": total_bets, "total_wins": total_wins,
                  "win_streak": rpg["win_streak"], "dark_horse_wins": rpg["dark_horse_wins"]},
        "xp_history": [{"amount": x[0], "reason": x[1], "date": x[2]} for x in xp_history],
    }


@router.get("/level")
async def get_level(authorization: str = Header(None)):
    """Quick level check."""
    user = await get_current_user(authorization)
    rpg = await _get_user_rpg(user["username"])
    return level_from_xp(rpg["xp"])


@router.post("/xp")
async def grant_xp(body: dict, authorization: str = Header(None)):
    """Grant XP for an action (called internally after bets resolve)."""
    user = await get_current_user(authorization)
    action = body.get("action", "")
    streak = body.get("streak", 0)
    odds = body.get("odds", 1.0)
    amount = calculate_xp_reward(action, streak, odds)
    if amount != 0:
        await _add_xp(user["username"], amount, action)
    rpg = await _get_user_rpg(user["username"])
    return {"xp_gained": amount, "total_xp": rpg["xp"], **level_from_xp(rpg["xp"])}


@router.post("/status")
async def set_status(body: dict, authorization: str = Header(None)):
    """Set online status."""
    user = await get_current_user(authorization)
    status = body.get("status", "online")
    if status not in STATUS_TYPES:
        raise HTTPException(400, f"Invalid status. Options: {list(STATUS_TYPES.keys())}")
    db = await get_db()
    try:
        await db.execute("UPDATE user_rpg SET status = ? WHERE username = ?", (status, user["username"]))
        await db.commit()
    finally:
        await db.close()
    return {"status": status, **STATUS_TYPES[status]}


@router.post("/frame")
async def set_frame(body: dict, authorization: str = Header(None)):
    """Set avatar frame."""
    user = await get_current_user(authorization)
    frame_id = body.get("frame", "silverstone")
    if frame_id not in FRAMES:
        raise HTTPException(400, "Invalid frame")
    rpg = await _get_user_rpg(user["username"])
    level_info = level_from_xp(rpg["xp"])
    if FRAMES[frame_id]["min_level"] > level_info["level"]:
        raise HTTPException(400, f"需要等級 {FRAMES[frame_id]['min_level']} 才能使用此外框")
    db = await get_db()
    try:
        await db.execute("UPDATE user_rpg SET frame = ? WHERE username = ?", (frame_id, user["username"]))
        await db.commit()
    finally:
        await db.close()
    return {"frame": frame_id, **FRAMES[frame_id]}


@router.get("/titles")
async def available_titles():
    """List all auto-titles."""
    return {"titles": [{"id": k, **v} for k, v in AUTO_TITLES.items()]}


@router.get("/frames")
async def available_frames():
    """List all frames."""
    return {"frames": [{"id": k, **v} for k, v in FRAMES.items()]}


@router.get("/leaderboard")
async def rpg_leaderboard():
    """RPG leaderboard by level/XP."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT username, xp, win_streak, frame, status FROM user_rpg ORDER BY xp DESC LIMIT 50"
        )
        leaders = []
        for i, r in enumerate(rows):
            lvl = level_from_xp(r[1])
            leaders.append({
                "rank": i + 1,
                "username": r[0],
                "level": lvl["level"],
                "title": lvl["title"],
                "xp": r[1],
                "win_streak": r[2],
                "frame": r[3],
                "status": r[4],
                "status_info": STATUS_TYPES.get(r[4], STATUS_TYPES["online"]),
            })
        return {"leaderboard": leaders}
    finally:
        await db.close()
