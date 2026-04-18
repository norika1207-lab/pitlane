"""Friend Challenge Rooms"""
import secrets
from fastapi import APIRouter, HTTPException, Header
from database import get_db
from routes.auth import get_current_user
from services.usdclaw import debit, credit, get_balance
from services.odds_engine import apply_fee

router = APIRouter(prefix="/api/challenge", tags=["challenge"])


@router.post("/create")
async def create_challenge(body: dict, authorization: str = Header(None)):
    """Create a challenge room"""
    user = await get_current_user(authorization)
    username = user["username"]
    race_id = body.get("race_id", "")
    race_name = body.get("race_name", "")
    amount = float(body.get("amount", 500))
    creator_pick = body.get("prediction", "")

    if amount < 1000 or amount > 500000:
        raise HTTPException(400, "Amount must be between 100 and 50000")

    fee_info = apply_fee(amount, "challenge_room")
    balance = await get_balance(username)
    if balance < fee_info["total"]:
        raise HTTPException(400, f"Insufficient Pit balance")

    await debit(username, fee_info["total"], "challenge_create", f"challenge:{race_id}")
    code = secrets.token_hex(4).upper()

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO challenges (code, creator, race_id, race_name, amount, creator_pick)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code, username, race_id, race_name, amount, creator_pick),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "code": code,
        "share_link": f"/battle?code={code}",
        "amount": amount,
        "fee": fee_info["fee"],
        "your_pick": creator_pick,
        "status": "waiting",
        "message": f"Share invite code {code} with your friend!",
    }


@router.get("/{code}")
async def get_challenge(code: str):
    """View a challenge room"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM challenges WHERE code = ?", (code,)
        )
        if not rows:
            raise HTTPException(404, "Challenge room not found")
        r = rows[0]
        return {
            "code": r[1], "creator": r[2], "race_id": r[3], "race_name": r[4],
            "amount": r[5], "creator_pick": r[7], "joiner": r[8],
            "joiner_pick": r[9], "status": r[10], "winner": r[11],
        }
    finally:
        await db.close()


@router.post("/join")
async def join_challenge(body: dict, authorization: str = Header(None)):
    """Join a challenge"""
    user = await get_current_user(authorization)
    username = user["username"]
    code = body.get("code", "")
    joiner_pick = body.get("prediction", "")

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM challenges WHERE code = ? AND status = 'waiting'", (code,)
        )
        if not rows:
            raise HTTPException(404, "Room not found or already full")
        challenge = rows[0]
        if challenge[2] == username:
            raise HTTPException(400, "Cannot challenge yourself")
        if joiner_pick == challenge[7]:
            raise HTTPException(400, "Cannot pick the same driver as your opponent")

        amount = challenge[5]
        fee_info = apply_fee(amount, "challenge_room")
        balance = await get_balance(username)
        if balance < fee_info["total"]:
            raise HTTPException(400, "Insufficient Pit balance")

        await debit(username, fee_info["total"], "challenge_join", f"challenge_join:{code}")

        await db.execute(
            "UPDATE challenges SET joiner = ?, joiner_pick = ?, status = 'active' WHERE code = ?",
            (username, joiner_pick, code),
        )
        await db.commit()

        return {
            "code": code,
            "opponent": challenge[2],
            "opponent_pick": challenge[7],
            "your_pick": joiner_pick,
            "amount": amount,
            "total_pool": amount * 2,
            "status": "active",
        }
    finally:
        await db.close()


@router.get("/my/list")
async def my_challenges(authorization: str = Header(None)):
    """My challenge history"""
    user = await get_current_user(authorization)
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT code, creator, race_name, amount, creator_pick, joiner, joiner_pick,
                      status, winner, created_at
               FROM challenges WHERE creator = ? OR joiner = ? ORDER BY created_at DESC LIMIT 50""",
            (user["username"], user["username"]),
        )
        return {"challenges": [
            {"code": r[0], "creator": r[1], "race_name": r[2], "amount": r[3],
             "creator_pick": r[4], "joiner": r[5], "joiner_pick": r[6],
             "status": r[7], "winner": r[8], "created_at": r[9]}
            for r in rows
        ]}
    finally:
        await db.close()
