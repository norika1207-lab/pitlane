"""Auth — Shared exchange account system
   Login forwards to exchange API, shared JWT token verification"""
from fastapi import APIRouter, HTTPException, Header
from jose import jwt, JWTError
import httpx
from config import JWT_SECRET, JWT_ALGORITHM
from services.usdclaw import get_user, get_balance
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

TRADING_API = "http://127.0.0.1:8010"


class LoginRequest(BaseModel):
    username: str
    password: str = ""

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


def decode_token(token: str) -> dict:
    """Verify exchange JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "Invalid token")
        return {"sub": username}
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user(authorization: str = Header(None)) -> dict:
    """Get current user from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in (use your exchange account)")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    username = payload["sub"]

    user = await get_user(username)
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("status") == "suspended":
        raise HTTPException(403, "Account suspended")

    return {"username": username, "balance": user.get("balance", 0)}


@router.post("/login")
async def login(data: LoginRequest):
    """Login — forward to exchange /api/token to get JWT"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{TRADING_API}/api/token",
                data={"username": data.username, "password": data.password},
                timeout=10,
            )
        except httpx.ConnectError:
            raise HTTPException(503, "Auth service unavailable")

    if resp.status_code != 200:
        raise HTTPException(401, "Invalid username or password")

    result = resp.json()
    token = result.get("access_token")
    username = result.get("username")

    # Get Pit balance
    balance = await get_balance(username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "balance": balance,
        "currency": "Pit",
    }


@router.post("/register")
async def register(data: RegisterRequest):
    """Register — forward to exchange /api/register, auto-login after success to get JWT"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{TRADING_API}/api/register",
                json={"username": data.username, "email": data.email, "password": data.password},
                timeout=10,
            )
        except httpx.ConnectError:
            raise HTTPException(503, "Auth service unavailable")

    if resp.status_code not in (200, 201):
        detail = "Registration failed — username or email already taken"
        try:
            body = resp.json()
            raw = body["detail"][0].get("msg", "") if isinstance(body.get("detail"), list) else body.get("detail", "")
            if "username" in raw.lower() or "2-30" in raw:
                detail = "Username must be 2–30 alphanumeric characters"
            elif "email" in raw.lower():
                detail = "Invalid email address"
            elif "密碼" in raw or "password" in raw.lower() or "8" in raw:
                detail = "Password must be 8–72 characters with letters and numbers"
        except Exception:
            pass
        raise HTTPException(400, detail)

    # Auto-login after registration
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f"{TRADING_API}/api/token",
            data={"username": data.username, "password": data.password},
            timeout=10,
        )

    if login_resp.status_code != 200:
        return {"message": "Registration successful, please log in manually"}

    result = login_resp.json()
    token = result.get("access_token")
    username = result.get("username")
    balance = await get_balance(username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "balance": balance,
        "currency": "Pit",
        "message": "Registration successful",
    }


@router.get("/me")
async def me(authorization: str = Header(None)):
    """Get current user info and Pit balance"""
    user = await get_current_user(authorization)
    balance = await get_balance(user["username"])
    return {
        "username": user["username"],
        "balance": balance,
        "currency": "Pit",
    }
