import os

# Server
HOST = "0.0.0.0"
PORT = 8002
BASE_PATH = "/racing"

# Database — Throttenix local data (bets, cache)
DB_PATH = "/opt/racing/pitlane.db"

# MongoDB — shared exchange accounts and USDClaw
MONGO_URI = "mongodb://clawApp:9SoPkGneSXeT11stDJnYvwnzjTaYWTy0woXUwyDMuM4@127.0.0.1:27017/?authSource=admin"

# JWT — shared exchange JWT secret, validates the same token
JWT_SECRET = "1d5aea0d4aa78cdb7cf89e61e74b81ced211fe9cfb91e6d5d343c82fda77961d"
JWT_ALGORITHM = "HS256"

# APIs
OPENF1_BASE = "https://api.openf1.org/v1"
ERGAST_BASE = "https://ergast.com/api/f1"

# Game
BET_MIN = 1000
BET_MAX = 500000

# Fee structure
FEE_CONFIG = {
    "system_bet": 0.05,
    "p2p_maker": 0.01,
    "p2p_taker": 0.02,
    "challenge_room": 0.03,
    "season_bet": 0.04,
}

# Card rarity tiers
RARITY = {
    "silverstone": {"name": "Silverstone", "level": 1, "label": "Starter"},
    "monza": {"name": "Monza", "level": 2, "label": "Advanced"},
    "suzuka": {"name": "Suzuka", "level": 3, "label": "Classic"},
    "monaco": {"name": "Monaco", "level": 4, "label": "Legend"},
}
