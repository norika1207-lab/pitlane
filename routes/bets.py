"""Bets — Place USDClaw bets predicting F1 race results"""
from fastapi import APIRouter, HTTPException, Header
from models import BetCreate
from database import get_db
from config import BET_MIN, BET_MAX
from routes.auth import get_current_user
from services.usdclaw import debit, credit, get_balance
from services.card_engine import calculate_driver_card, calculate_odds

router = APIRouter(prefix="/api/bets", tags=["bets"])


@router.post("")
async def place_bet(bet: BetCreate, authorization: str = Header(None)):
    """Place a bet using USDClaw"""
    user = await get_current_user(authorization)
    username = user["username"]

    if bet.amount < BET_MIN or bet.amount > BET_MAX:
        raise HTTPException(400, f"Bet must be between {BET_MIN} and {BET_MAX} USDClaw")

    balance = await get_balance(username)
    if balance < bet.amount:
        raise HTTPException(400, f"Insufficient USDClaw balance. Current balance: {balance:,.0f}")

    # Calculate odds
    stats = await calculate_driver_card(bet.prediction)
    odds = calculate_odds(stats)

    # Deduct USDClaw via trading platform's token system
    ref_id = f"throttenix_bet:{bet.race_id}:{bet.prediction}"
    try:
        await debit(username, bet.amount, "throttenix_bet", ref_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Record bet in Throttenix's SQLite
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO bets (username, race_id, race_name, bet_type, prediction, amount, odds)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, bet.race_id, bet.race_name, bet.bet_type, bet.prediction, bet.amount, odds),
        )
        await db.commit()
    finally:
        await db.close()

    new_balance = await get_balance(username)
    return {
        "message": "Bet placed!",
        "amount": bet.amount,
        "odds": odds,
        "potential_win": int(bet.amount * odds),
        "remaining_balance": new_balance,
        "currency": "USDClaw",
    }


@router.get("/my")
async def my_bets(authorization: str = Header(None)):
    """Get bet history"""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, race_id, race_name, bet_type, prediction, amount, odds,
                      result, payout, created_at
               FROM bets WHERE username = ? ORDER BY created_at DESC LIMIT 50""",
            (user["username"],),
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
    """View bet results for a specific race"""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, prediction, amount, odds, result, payout
               FROM bets WHERE username = ? AND race_id = ?""",
            (user["username"], race_id),
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
