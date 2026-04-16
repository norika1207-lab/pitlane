import aiosqlite
from config import DB_PATH

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
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
            fee REAL DEFAULT 0,
            odds REAL DEFAULT 1.0,
            result TEXT DEFAULT 'pending',
            payout REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS p2p_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator TEXT NOT NULL,
            race_id TEXT NOT NULL,
            race_name TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            prediction TEXT NOT NULL,
            odds REAL NOT NULL,
            amount REAL NOT NULL,
            fee REAL DEFAULT 0,
            taker TEXT,
            taker_amount REAL DEFAULT 0,
            taker_fee REAL DEFAULT 0,
            status TEXT DEFAULT 'open',
            result TEXT DEFAULT 'pending',
            winner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            creator TEXT NOT NULL,
            race_id TEXT NOT NULL,
            race_name TEXT NOT NULL,
            amount REAL NOT NULL,
            fee_rate REAL DEFAULT 0.03,
            creator_pick TEXT NOT NULL,
            joiner TEXT,
            joiner_pick TEXT,
            status TEXT DEFAULT 'waiting',
            winner TEXT,
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
        CREATE INDEX IF NOT EXISTS idx_p2p_status ON p2p_orders(status);
        CREATE INDEX IF NOT EXISTS idx_challenge_code ON challenges(code);
    """)
    await db.commit()
    await db.close()
