"""Profile — Stats and Leaderboard"""
from fastapi import APIRouter, HTTPException, Header
from database import get_db
from routes.auth import get_current_user
from services.usdclaw import get_balance
from services.card_engine import determine_rarity
from config import RARITY

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
async def my_profile(authorization: str = Header(None)):
    """Get personal stats"""
    user = await get_current_user(authorization)
    username = user["username"]
    balance = await get_balance(username)

    db = await get_db()
    try:
        # Get bet stats from SQLite
        row = await db.execute_fetchall(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins
               FROM bets WHERE username = ?""",
            (username,),
        )
        total_bets = row[0][0] if row else 0
        total_wins = row[0][1] or 0 if row else 0
        win_rate = total_wins / total_bets * 100 if total_bets > 0 else 0

        rarity = determine_rarity({"total_bets": total_bets, "total_wins": total_wins})
        rarity_info = RARITY.get(rarity, RARITY["silverstone"])

        return {
            "username": username,
            "balance": balance,
            "currency": "USDClaw",
            "total_bets": total_bets,
            "total_wins": total_wins,
            "win_rate": round(win_rate, 1),
            "rarity_level": rarity,
            "rarity_name": rarity_info["name"],
            "rarity_label": rarity_info["label"],
        }
    finally:
        await db.close()


@router.get("/sharecard")
async def share_card(authorization: str = Header(None)):
    """Generate shareable stats card data"""
    user = await get_current_user(authorization)
    username = user["username"]
    balance = await get_balance(username)

    db = await get_db()
    try:
        row = await db.execute_fetchall(
            """SELECT COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END)
               FROM bets WHERE username = ?""",
            (username,),
        )
        total_bets = row[0][0] if row else 0
        total_wins = row[0][1] or 0 if row else 0
        win_rate = total_wins / total_bets * 100 if total_bets > 0 else 0

        recent = await db.execute_fetchall(
            """SELECT race_name, prediction, result, payout
               FROM bets WHERE username = ? ORDER BY created_at DESC LIMIT 5""",
            (username,),
        )

        rarity = determine_rarity({"total_bets": total_bets, "total_wins": total_wins})
        rarity_info = RARITY.get(rarity, RARITY["silverstone"])

        return {
            "username": username,
            "balance": balance,
            "currency": "USDClaw",
            "total_bets": total_bets,
            "total_wins": total_wins,
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
    """Throttenix betting leaderboard"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT username,
                      COUNT(*) as total_bets,
                      SUM(CASE WHEN result='won' THEN 1 ELSE 0 END) as wins,
                      SUM(payout) as total_payout
               FROM bets
               GROUP BY username
               ORDER BY total_payout DESC, wins DESC
               LIMIT 50"""
        )
        leaders = []
        for i, r in enumerate(rows):
            total = r[1]
            wins = r[2] or 0
            leaders.append({
                "rank": i + 1,
                "username": r[0],
                "total_bets": total,
                "total_wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "total_payout": r[3] or 0,
            })
        return {"leaderboard": leaders}
    finally:
        await db.close()
