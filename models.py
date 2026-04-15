from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BetCreate(BaseModel):
    race_id: str
    race_name: str
    bet_type: str  # "winner"
    prediction: str  # driver_id
    amount: int

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    coins: int

class DriverCard(BaseModel):
    driver_id: str
    name: str
    team: str
    number: Optional[str] = None
    nationality: Optional[str] = None
    rarity: str = "silverstone"
    stats: dict = {}

class RaceInfo(BaseModel):
    race_id: str
    race_name: str
    circuit: str
    date: str
    country: str
    round: int
