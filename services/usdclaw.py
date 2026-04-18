"""Pit token client — thin HTTP wrapper around shared_auth (port 8010).

All account and token operations are delegated to the canonical service;
racing never touches MongoDB directly.
"""
import httpx
from config import SHARED_AUTH_URL, SERVICE_KEY

_HEADERS = {"x-service-key": SERVICE_KEY}
_TIMEOUT = 10


async def get_user(username: str) -> dict | None:
    """Return user info dict or None if not found."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{SHARED_AUTH_URL}/api/service/user/{username}",
                        headers=_HEADERS, timeout=_TIMEOUT)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


async def get_balance(username: str) -> float:
    user = await get_user(username)
    return user.get("balance", 0.0) if user else 0.0


async def debit(username: str, amount: float, reason: str, ref_id: str = ""):
    """Debit Pit tokens. Raises ValueError on insufficient balance."""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{SHARED_AUTH_URL}/api/service/pit/debit",
            json={"username": username, "amount": amount,
                  "reason": reason, "ref_id": ref_id},
            headers=_HEADERS, timeout=_TIMEOUT,
        )
    if r.status_code == 400:
        raise ValueError(r.json().get("detail", "Insufficient Pit balance"))
    r.raise_for_status()
    return r.json()


async def credit(username: str, amount: float, reason: str, ref_id: str = ""):
    """Credit Pit tokens. Returns token_id."""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{SHARED_AUTH_URL}/api/service/pit/credit",
            json={"username": username, "amount": amount,
                  "reason": reason, "ref_id": ref_id},
            headers=_HEADERS, timeout=_TIMEOUT,
        )
    r.raise_for_status()
    return r.json().get("token_id", "")
