import os

# Server
HOST = "0.0.0.0"
PORT = 8002
BASE_PATH = "/racing"

# Database — PitLane 自己的資料 (bets, cache)
DB_PATH = "/opt/racing/pitlane.db"

# MongoDB — 共用交易所的帳號和 USDClaw
MONGO_URI = "mongodb://clawApp:9SoPkGneSXeT11stDJnYvwnzjTaYWTy0woXUwyDMuM4@127.0.0.1:27017/?authSource=admin"

# JWT — 共用交易所的 JWT secret，驗證同一個 token
JWT_SECRET = "1d5aea0d4aa78cdb7cf89e61e74b81ced211fe9cfb91e6d5d343c82fda77961d"
JWT_ALGORITHM = "HS256"

# APIs
OPENF1_BASE = "https://api.openf1.org/v1"
ERGAST_BASE = "https://ergast.com/api/f1"

# Game
BET_MIN = 100
BET_MAX = 50000

# Card rarity tiers
RARITY = {
    "silverstone": {"name": "銀石 Silverstone", "level": 1, "label": "入門"},
    "monza": {"name": "蒙扎 Monza", "level": 2, "label": "進階"},
    "suzuka": {"name": "鈴鹿 Suzuka", "level": 3, "label": "經典"},
    "monaco": {"name": "摩納哥 Monaco", "level": 4, "label": "傳奇"},
}
