"""USDClaw 接口 — 連接交易所的 MongoDB，共用帳號和虛擬幣
   完全複製交易所的 debit/credit 邏輯，維持帳本鏈完整性"""

import hashlib
import secrets
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

_client = AsyncIOMotorClient(MONGO_URI)
db_users = _client["claw_users"]
db_usdclaw = _client["claw_usdclaw"]


def _generate_token_id(username, amount, timestamp):
    raw = f"{username}:{amount}:{timestamp}:{secrets.token_hex(16)}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_user(username: str) -> dict | None:
    """從交易所 DB 取得用戶資料"""
    return await db_users.assets.find_one({"username": username})


async def get_balance(username: str) -> float:
    """取得 USDClaw 餘額"""
    user = await db_users.assets.find_one({"username": username})
    if not user:
        return 0.0
    return user.get("balance", 0.0)


async def _write_ledger(username, tx_type, amount, reason, ref_id, now):
    """寫入帳本鏈（與交易所完全相同的邏輯）"""
    last = await db_usdclaw.ledger.find_one({"username": username}, sort=[("seq", -1)])
    seq = (last["seq"] + 1) if last else 1
    prev_hash = last["checksum"] if last else "0" * 64
    entry = {
        "username": username, "seq": seq,
        "type": tx_type, "amount": amount,
        "reason": reason, "ref_id": ref_id,
        "time": now, "prev_hash": prev_hash
    }
    entry["checksum"] = hashlib.sha256(
        f"{username}:{seq}:{tx_type}:{amount}:{reason}:{prev_hash}:{now.isoformat()}".encode()
    ).hexdigest()
    await db_usdclaw.ledger.insert_one(entry)
    return entry


async def debit(username: str, amount: float, reason: str, ref_id: str = ""):
    """扣除 USDClaw（與交易所相同的 FIFO token 消耗邏輯）"""
    now = datetime.utcnow()
    await _write_ledger(username, "debit", amount, reason, ref_id, now)

    # FIFO: 先消耗不可轉帳的，再消耗可轉帳的
    remaining = amount
    for transferable_flag in [False, True]:
        if remaining <= 0:
            break
        cursor = db_usdclaw.tokens.find({
            "owner": username,
            "status": "active",
            "transferable": transferable_flag
        }).sort("created_at", 1)
        async for tok in cursor:
            if remaining <= 0:
                break
            use_amount = min(tok["amount"], remaining)
            remaining -= use_amount
            new_amount = round(tok["amount"] - use_amount, 2)
            history_entry = {
                "action": "debit",
                "reason": reason,
                "ref_id": ref_id,
                "amount": use_amount,
                "remaining": new_amount,
                "time": now
            }
            if new_amount <= 0:
                await db_usdclaw.tokens.update_one(
                    {"token_id": tok["token_id"]},
                    {"$set": {"status": "spent", "amount": 0},
                     "$push": {"history": history_entry}}
                )
            else:
                await db_usdclaw.tokens.update_one(
                    {"token_id": tok["token_id"]},
                    {"$set": {"amount": new_amount},
                     "$push": {"history": history_entry}}
                )

    # Atomic balance deduction
    result = await db_users.assets.find_one_and_update(
        {"username": username, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount}}
    )
    if not result:
        raise ValueError("Insufficient USDClaw balance")


async def credit(username: str, amount: float, reason: str, ref_id: str = ""):
    """入帳 USDClaw（獎金回饋，可轉帳）"""
    now = datetime.utcnow()
    await _write_ledger(username, "credit", amount, reason, ref_id, now)

    token_id = _generate_token_id(username, amount, now.isoformat())
    token_doc = {
        "token_id": token_id,
        "amount": amount,
        "original_amount": amount,
        "owner": username,
        "status": "active",
        "origin": reason,
        "transferable": True,  # PitLane 獎金可轉帳
        "created_at": now,
        "history": [{
            "action": "created",
            "from": "pitlane",
            "to": username,
            "amount": amount,
            "origin": reason,
            "ref_id": ref_id,
            "time": now
        }]
    }
    await db_usdclaw.tokens.insert_one(token_doc)
    await db_users.assets.update_one({"username": username}, {"$inc": {"balance": amount}})
    return token_id
