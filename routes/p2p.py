"""P2P Betting System"""
import secrets
from fastapi import APIRouter, HTTPException, Header
from database import get_db
from routes.auth import get_current_user
from services.usdclaw import debit, credit, get_balance
from services.odds_engine import apply_fee

router = APIRouter(prefix="/api/p2p", tags=["p2p"])


@router.post("/create")
async def create_order(body: dict, authorization: str = Header(None)):
    """Place order: bet on a driver with specified odds and amount"""
    user = await get_current_user(authorization)
    username = user["username"]
    race_id = body.get("race_id", "")
    race_name = body.get("race_name", "")
    bet_type = body.get("bet_type", "winner")
    prediction = body.get("prediction", "")
    odds = float(body.get("odds", 2.0))
    amount = float(body.get("amount", 500))

    if amount < 1000 or amount > 500000:
        raise HTTPException(400, "Amount must be between 100 and 50000")
    if odds < 1.1 or odds > 50.0:
        raise HTTPException(400, "Odds must be between 1.1 and 50.0")

    fee_info = apply_fee(amount, "p2p_maker")
    balance = await get_balance(username)
    if balance < fee_info["total"]:
        raise HTTPException(400, f"Insufficient USDClaw balance (need {fee_info['total']:,.0f})")

    await debit(username, fee_info["total"], "p2p_create", f"p2p:{race_id}:{prediction}")

    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO p2p_orders (creator, race_id, race_name, bet_type, prediction, odds, amount, fee)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, race_id, race_name, bet_type, prediction, odds, amount, fee_info["fee"]),
        )
        await db.commit()
        order_id = cursor.lastrowid
    finally:
        await db.close()

    return {
        "order_id": order_id,
        "amount": amount,
        "fee": fee_info["fee"],
        "odds": odds,
        "prediction": prediction,
        "status": "open",
        "waiting_for": f"Waiting for opponent to stake {amount * (odds - 1):,.0f} USDClaw",
    }


@router.get("/available")
async def available_orders(authorization: str = Header(None)):
    """View available orders to accept"""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, creator, race_id, race_name, bet_type, prediction, odds, amount, created_at
               FROM p2p_orders WHERE status = 'open' AND creator != ? ORDER BY created_at DESC LIMIT 50""",
            (user["username"],),
        )
        return {"orders": [
            {"id": r[0], "creator": r[1], "race_id": r[2], "race_name": r[3],
             "bet_type": r[4], "prediction": r[5], "odds": r[6], "amount": r[7],
             "taker_amount": round(r[7] * (r[6] - 1), 2), "created_at": r[8]}
            for r in rows
        ]}
    finally:
        await db.close()


@router.post("/accept/{order_id}")
async def accept_order(order_id: int, authorization: str = Header(None)):
    """Accept an order"""
    user = await get_current_user(authorization)
    username = user["username"]

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM p2p_orders WHERE id = ? AND status = 'open'", (order_id,)
        )
        if not rows:
            raise HTTPException(404, "Order not found or already taken")
        order = rows[0]
        if order[1] == username:  # creator
            raise HTTPException(400, "Cannot accept your own order")

        taker_amount = round(order[7] * (order[6] - 1), 2)  # amount * (odds - 1)
        fee_info = apply_fee(taker_amount, "p2p_taker")
        balance = await get_balance(username)
        if balance < fee_info["total"]:
            raise HTTPException(400, f"Insufficient USDClaw balance (need {fee_info['total']:,.0f})")

        await debit(username, fee_info["total"], "p2p_accept", f"p2p_accept:{order_id}")

        await db.execute(
            """UPDATE p2p_orders SET taker = ?, taker_amount = ?, taker_fee = ?, status = 'matched'
               WHERE id = ?""",
            (username, taker_amount, fee_info["fee"], order_id),
        )
        await db.commit()

        return {
            "order_id": order_id,
            "your_amount": taker_amount,
            "your_fee": fee_info["fee"],
            "opponent": order[1],
            "prediction": order[5],
            "odds": order[6],
            "status": "matched",
            "total_pool": round(order[7] + taker_amount, 2),
        }
    finally:
        await db.close()


@router.get("/my")
async def my_orders(authorization: str = Header(None)):
    """My P2P order history"""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT id, creator, race_name, prediction, odds, amount, taker, taker_amount,
                      status, result, winner, created_at
               FROM p2p_orders WHERE creator = ? OR taker = ? ORDER BY created_at DESC LIMIT 50""",
            (user["username"], user["username"]),
        )
        return {"orders": [
            {"id": r[0], "creator": r[1], "race_name": r[2], "prediction": r[3],
             "odds": r[4], "amount": r[5], "taker": r[6], "taker_amount": r[7],
             "status": r[8], "result": r[9], "winner": r[10], "created_at": r[11],
             "role": "maker" if r[1] == user["username"] else "taker"}
            for r in rows
        ]}
    finally:
        await db.close()
