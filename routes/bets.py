from fastapi import APIRouter, HTTPException, Header
from models import BetCreate
from database import get_db
from config import BET_MIN, BET_MAX
from routes.auth import decode_token
from services.card_engine import calculate_driver_card, calculate_odds

router = APIRouter(prefix="/api/bets", tags=["bets"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    return payload


@router.post("")
async def place_bet(bet: BetCreate, authorization: str = Header(None)):
    """Place a prediction bet."""
    user = await get_current_user(authorization)
    user_id = int(user["sub"])

    if bet.amount < BET_MIN or bet.amount > BET_MAX:
        raise HTTPException(400, f"Bet must be between {BET_MIN} and {BET_MAX}")

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT coins FROM users WHERE id = ?", (user_id,)
        )
        if not rows:
            raise HTTPException(404, "User not found")
        coins = rows[0][0]
        if coins < bet.amount:
            raise HTTPException(400, f"Not enough coins. You have {coins}")

        # Calculate odds
        stats = await calculate_driver_card(bet.prediction)
        odds = calculate_odds(stats)

        # Deduct coins
        await db.execute(
            "UPDATE users SET coins = coins - ? WHERE id = ?",
            (bet.amount, user_id),
        )

        # Create bet
        await db.execute(
            """INSERT INTO bets (user_id, race_id, race_name, bet_type, prediction, amount, odds)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, bet.race_id, bet.race_name, bet.bet_type, bet.prediction, bet.amount, odds),
        )

        await db.execute(
            "UPDATE users SET total_bets = total_bets + 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()

        new_coins = coins - bet.amount
        return {
            "message": "Bet placed!",
            "amount": bet.amount,
            "odds": odds,
            "potential_win": int(bet.amount * odds),
            "remaining_coins": new_coins,
        }
    finally:
        await db.close()


@router.get("/my")
async def my_bets(authorization: str = Header(None)):
    """Get user's betting history."""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, race_id, race_name, bet_type, prediction, amount, odds,
                      result, payout, created_at
               FROM bets WHERE user_id = ? ORDER BY created_at DESC LIMIT 50""",
            (user["sub"],),
        )
        bets = []
        for r in rows:
            bets.append({
                "id": r[0], "race_id": r[1], "race_name": r[2],
                "bet_type": r[3], "prediction": r[4], "amount": r[5],
                "odds": r[6], "result": r[7], "payout": r[8],
                "created_at": r[9],
            })
        return {"bets": bets}
    finally:
        await db.close()


@router.get("/{race_id}/result")
async def bet_result(race_id: str, authorization: str = Header(None)):
    """Check bet results for a specific race."""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, prediction, amount, odds, result, payout
               FROM bets WHERE user_id = ? AND race_id = ?""",
            (user["sub"], race_id),
        )
        bets = []
        for r in rows:
            bets.append({
                "id": r[0], "prediction": r[1], "amount": r[2],
                "odds": r[3], "result": r[4], "payout": r[5],
            })
        return {"race_id": race_id, "bets": bets}
    finally:
        await db.close()
