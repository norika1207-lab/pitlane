from fastapi import APIRouter, HTTPException, Header
from database import get_db
from routes.auth import decode_token
from services.card_engine import determine_rarity
from config import RARITY

router = APIRouter(prefix="/api/profile", tags=["profile"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ")[1]
    return decode_token(token)


@router.get("")
async def my_profile(authorization: str = Header(None)):
    """Get user profile with stats."""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT username, email, coins, total_bets, total_wins,
                      rarity_level, created_at FROM users WHERE id = ?""",
            (user["sub"],),
        )
        if not rows:
            raise HTTPException(404, "User not found")
        u = rows[0]
        win_rate = u[4] / u[3] * 100 if u[3] > 0 else 0
        rarity = determine_rarity({
            "total_bets": u[3], "total_wins": u[4]
        })
        rarity_info = RARITY.get(rarity, RARITY["silverstone"])

        return {
            "username": u[0],
            "email": u[1],
            "coins": u[2],
            "total_bets": u[3],
            "total_wins": u[4],
            "win_rate": round(win_rate, 1),
            "rarity_level": rarity,
            "rarity_name": rarity_info["name"],
            "rarity_label": rarity_info["label"],
            "joined": u[6],
        }
    finally:
        await db.close()


@router.get("/sharecard")
async def share_card(authorization: str = Header(None)):
    """Generate data for a shareable stats card."""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT username, coins, total_bets, total_wins, rarity_level
               FROM users WHERE id = ?""",
            (user["sub"],),
        )
        if not rows:
            raise HTTPException(404, "User not found")
        u = rows[0]

        # Get recent bet results
        recent = await db.execute_fetchall(
            """SELECT race_name, prediction, result, payout
               FROM bets WHERE user_id = ? ORDER BY created_at DESC LIMIT 5""",
            (user["sub"],),
        )

        win_rate = u[3] / u[2] * 100 if u[2] > 0 else 0
        rarity = determine_rarity({"total_bets": u[2], "total_wins": u[3]})
        rarity_info = RARITY.get(rarity, RARITY["silverstone"])

        return {
            "username": u[0],
            "coins": u[1],
            "total_bets": u[2],
            "total_wins": u[3],
            "win_rate": round(win_rate, 1),
            "rarity_level": rarity,
            "rarity_name": rarity_info["name"],
            "recent_bets": [
                {"race": r[0], "prediction": r[1], "result": r[2], "payout": r[3]}
                for r in recent
            ],
        }
    finally:
        await db.close()


@router.get("/leaderboard")
async def leaderboard():
    """Global leaderboard."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT username, coins, total_bets, total_wins
               FROM users ORDER BY coins DESC LIMIT 50"""
        )
        leaders = []
        for i, r in enumerate(rows):
            leaders.append({
                "rank": i + 1,
                "username": r[0],
                "coins": r[1],
                "total_bets": r[2],
                "total_wins": r[3],
                "win_rate": round(r[3] / r[2] * 100, 1) if r[2] > 0 else 0,
            })
        return {"leaderboard": leaders}
    finally:
        await db.close()
