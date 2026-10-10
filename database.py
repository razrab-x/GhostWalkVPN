import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                order_id TEXT UNIQUE,
                amount INTEGER,
                plan TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS vpn_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                private_key TEXT,
                public_key TEXT,
                address TEXT,
                expires_at TIMESTAMP,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(tg_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, username) VALUES (?, ?)",
            (tg_id, username)
        )
        await db.commit()

async def create_payment(tg_id, order_id, amount, plan):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (tg_id, order_id, amount, plan) VALUES (?, ?, ?, ?)",
            (tg_id, order_id, amount, plan)
        )
        await db.commit()

async def confirm_payment(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status='paid' WHERE order_id=? AND status='pending'",
            (order_id,)
        )
        await db.commit()
        async with db.execute(
            "SELECT tg_id, plan FROM payments WHERE order_id=?", (order_id,)
        ) as cur:
            return await cur.fetchone()

async def get_payment_status(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT status FROM payments WHERE order_id=?", (order_id,)
        ) as cur:
            return await cur.fetchone()

async def add_vpn_key(tg_id, priv, pub, addr, expires_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO vpn_keys (tg_id, private_key, public_key, address, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (tg_id, priv, pub, addr, expires_at)
        )
        await db.commit()

async def get_user_keys(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, address, expires_at, active FROM vpn_keys WHERE tg_id=? ORDER BY id DESC",
            (tg_id,)
        ) as cur:
            return await cur.fetchall()

async def get_key_by_id(key_id, tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT private_key, public_key, address, expires_at FROM vpn_keys WHERE id=? AND tg_id=?",
            (key_id, tg_id)
        ) as cur:
            return await cur.fetchone()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM vpn_keys WHERE active=1") as cur:
            keys = (await cur.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'") as cur:
            total = (await cur.fetchone())[0]
    return users, keys, total
