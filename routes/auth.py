from fastapi import APIRouter, HTTPException
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from models import UserRegister, UserLogin, TokenResponse
from database import get_db
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS, STARTING_COINS

router = APIRouter(prefix="/api/auth", tags=["auth"])


def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    if len(data.username) < 2 or len(data.password) < 4:
        raise HTTPException(400, "Username min 2 chars, password min 4 chars")

    db = await get_db()
    try:
        existing = await db.execute_fetchall(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (data.username, data.email),
        )
        if existing:
            raise HTTPException(400, "Username or email already exists")

        salt = secrets.token_hex(16)
        pw_hash = hashlib.sha256((salt + data.password).encode()).hexdigest() + ":" + salt
        cursor = await db.execute(
            "INSERT INTO users (username, email, password_hash, coins) VALUES (?, ?, ?, ?)",
            (data.username, data.email, pw_hash, STARTING_COINS),
        )
        await db.commit()
        user_id = cursor.lastrowid
        token = create_token(user_id, data.username)
        return TokenResponse(
            access_token=token, username=data.username, coins=STARTING_COINS
        )
    finally:
        await db.close()


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT id, username, password_hash, coins FROM users WHERE username = ?",
            (data.username,),
        )
        if not rows:
            raise HTTPException(401, "Invalid credentials")
        user = rows[0]
        stored = user[2]
        parts = stored.split(":")
        if len(parts) != 2:
            raise HTTPException(401, "Invalid credentials")
        stored_hash, salt = parts
        check_hash = hashlib.sha256((salt + data.password).encode()).hexdigest()
        if check_hash != stored_hash:
            raise HTTPException(401, "Invalid credentials")

        token = create_token(user[0], user[1])
        return TokenResponse(
            access_token=token, username=user[1], coins=user[3]
        )
    finally:
        await db.close()
