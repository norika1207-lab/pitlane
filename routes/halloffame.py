"""routes/halloffame.py — Hall of Fame: legendary retired F1 driver card collection"""
from fastapi import APIRouter, HTTPException, Header
from database import get_db
from routes.auth import get_current_user, decode_token
from services.legend_data import LEGENDS, get_legend

router = APIRouter(prefix="/api/halloffame", tags=["halloffame"])


async def _get_user_total_bets(username: str) -> int:
    """Return the total number of bets placed by a user across all time."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT COUNT(*) FROM bets WHERE username = ?", (username,)
        )
        count = rows[0][0] if rows else 0
        # Also count p2p orders the user created or took
        rows2 = await db.execute_fetchall(
            "SELECT COUNT(*) FROM p2p_orders WHERE creator = ? OR taker = ?",
            (username, username),
        )
        count += rows2[0][0] if rows2 else 0
        return count
    finally:
        await db.close()


async def _get_user_claimed_ids(username: str) -> set:
    """Return set of legend_ids already claimed by the user."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT legend_id FROM halloffame_collection WHERE username = ?", (username,)
        )
        return {r[0] for r in rows}
    finally:
        await db.close()


@router.get("")
async def list_legends(authorization: str = Header(None)):
    """Return all legends. If authenticated, include claimed/eligible flags."""
    user_bets = 0
    claimed_ids: set = set()
    authed = False

    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = decode_token(token)
            username = payload["sub"]
            user_bets = await _get_user_total_bets(username)
            claimed_ids = await _get_user_claimed_ids(username)
            authed = True
        except Exception:
            pass

    result = []
    for legend in LEGENDS:
        entry = dict(legend)
        if authed:
            entry["claimed"] = legend["id"] in claimed_ids
            entry["eligible"] = user_bets >= legend["unlock_bets"]
        else:
            entry["claimed"] = False
            entry["eligible"] = False
        result.append(entry)

    return {
        "legends": result,
        "user_bets": user_bets,
        "authenticated": authed,
    }


@router.post("/claim/{legend_id}")
async def claim_legend(legend_id: str, authorization: str = Header(None)):
    """Claim a legend card. Requires auth and sufficient total bets."""
    user = await get_current_user(authorization)
    username = user["username"]

    legend = get_legend(legend_id)
    if not legend:
        raise HTTPException(404, f"Legend '{legend_id}' not found")

    # Check if already claimed
    claimed_ids = await _get_user_claimed_ids(username)
    if legend_id in claimed_ids:
        raise HTTPException(400, "你已經收藏這張卡片了")

    # Check total bets requirement
    user_bets = await _get_user_total_bets(username)
    if user_bets < legend["unlock_bets"]:
        shortage = legend["unlock_bets"] - user_bets
        raise HTTPException(
            400,
            f"堵注次數不足。需要 {legend['unlock_bets']} 次，目前 {user_bets} 次，還差 {shortage} 次。",
        )

    # Insert into collection
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO halloffame_collection (username, legend_id) VALUES (?, ?)",
            (username, legend_id),
        )
        await db.commit()
    except Exception:
        raise HTTPException(400, "收藏失敗，請重試")
    finally:
        await db.close()

    return {
        "success": True,
        "message": f"成功收藏 {legend['name']}！",
        "legend": legend,
        "user_bets": user_bets,
    }


@router.get("/collection")
async def user_collection(authorization: str = Header(None)):
    """Return all legend cards claimed by the authenticated user."""
    user = await get_current_user(authorization)
    username = user["username"]

    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT legend_id, claimed_at FROM halloffame_collection WHERE username = ? ORDER BY claimed_at ASC",
            (username,),
        )
    finally:
        await db.close()

    collected = []
    for row in rows:
        legend = get_legend(row[0])
        if legend:
            entry = dict(legend)
            entry["claimed"] = True
            entry["eligible"] = True
            entry["claimed_at"] = row[1]
            collected.append(entry)

    user_bets = await _get_user_total_bets(username)

    return {
        "username": username,
        "user_bets": user_bets,
        "count": len(collected),
        "collection": collected,
    }
