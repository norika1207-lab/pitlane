"""Auth — 共用交易所帳號系統
   登入透過轉發到交易所 API，JWT token 共用驗證"""
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
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


def decode_token(token: str) -> dict:
    """驗證交易所的 JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(401, "Invalid token")
        return {"sub": username}
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user(authorization: str = Header(None)) -> dict:
    """從 Authorization header 取得當前用戶"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "請先登入（使用交易所帳號）")
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
    """登入 — 轉發到交易所 /api/token 取得 JWT"""
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
        detail = "帳號或密碼錯誤"
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
    """註冊 — 轉發到交易所 /api/register，成功後自動登入取得 JWT"""
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
        detail = "註冊失敗"
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
        return {"message": "註冊成功，請手動登入"}

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
        "message": "註冊成功",
    }


@router.get("/me")
async def me(authorization: str = Header(None)):
    """取得當前用戶資訊和 USDClaw 餘額"""
    user = await get_current_user(authorization)
    balance = await get_balance(user["username"])
    return {
        "username": user["username"],
        "balance": balance,
        "currency": "USDClaw",
    }
