from pydantic import BaseModel
from typing import Optional


class BetCreate(BaseModel):
    race_id: str
    race_name: str
    bet_type: str  # "winner"
    prediction: str  # driver_id
    amount: float


class DriverCard(BaseModel):
    driver_id: str
    name: str
    team: str
    number: Optional[str] = None
    nationality: Optional[str] = None
    rarity: str = "silverstone"
    stats: dict = {}
