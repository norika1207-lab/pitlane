import aiosqlite
from config import DB_PATH

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    """PitLane 自己的資料（bets, cache）。用戶帳號走交易所 MongoDB。"""
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            race_id TEXT NOT NULL,
            race_name TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            prediction TEXT NOT NULL,
            amount REAL NOT NULL,
            odds REAL DEFAULT 1.0,
            result TEXT DEFAULT 'pending',
            payout REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS race_cache (
            key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_bets_username ON bets(username);
        CREATE INDEX IF NOT EXISTS idx_bets_race ON bets(race_id);
    """)
    await db.commit()
    await db.close()
