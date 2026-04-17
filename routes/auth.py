"""Auth — Shared exchange account system
   Login forwards to exchange API, shared JWT token verification"""
from fastapi import APIRouter, HTTPException, Header
from jose import jwt, JWTError
import httpx
from config import JWT_SECRET, JWT_ALGORITHM
from services.usdclaw import get_user, get_balance
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

TRADING_API = "http://127.0.0.1:8000"


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
            raise HTTPException(503, "Trading platform unavailable")

    if resp.status_code != 200:
        detail = "Invalid username or password"
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        raise HTTPException(401, detail)

    result = resp.json()
    token = result.get("access_token")
    username = result.get("username")

    # Get USDClaw balance
    balance = await get_balance(username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "balance": balance,
        "currency": "USDClaw",
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
            raise HTTPException(503, "Trading platform unavailable")

    if resp.status_code not in (200, 201):
        detail = "Registration failed"
        try:
            body = resp.json()
            if isinstance(body.get("detail"), list):
                detail = body["detail"][0].get("msg", detail)
            else:
                detail = body.get("detail", detail)
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
        "currency": "USDClaw",
        "message": "Registration successful",
    }


@router.get("/me")
async def me(authorization: str = Header(None)):
    """Get current user info and USDClaw balance"""
    user = await get_current_user(authorization)
    balance = await get_balance(user["username"])
    return {
        "username": user["username"],
        "balance": balance,
        "currency": "USDClaw",
    }
