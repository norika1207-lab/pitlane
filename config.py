import os

# Server
HOST = "0.0.0.0"
PORT = 8002
BASE_PATH = "/racing"

# Database
DB_PATH = "/opt/racing/pitlane.db"

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "pitlane_secret_key_change_in_prod_2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72

# APIs
OPENF1_BASE = "https://api.openf1.org/v1"
ERGAST_BASE = "https://ergast.com/api/f1"

# Game
STARTING_COINS = 10000
BET_MIN = 100
BET_MAX = 5000

# Card rarity tiers
RARITY = {
    "silverstone": {"name": "銀石 Silverstone", "level": 1, "label": "入門"},
    "monza": {"name": "蒙扎 Monza", "level": 2, "label": "進階"},
    "suzuka": {"name": "鈴鹿 Suzuka", "level": 3, "label": "經典"},
    "monaco": {"name": "摩納哥 Monaco", "level": 4, "label": "傳奇"},
}
