import asyncpg
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST", "airlines-server.postgres.database.azure.com"
)
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin_login")
POSTGRES_PASSWORD = quote(
    os.getenv("POSTGRES_PASSWORD", "saturam@123")
)  # encode special chars
POSTGRES_DB = os.getenv("POSTGRES_DB", "airlines")

DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Use a pool for production
_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DSN, min_size=1, max_size=10)
    return _pool


async def fetch_all(table_name: str):
    """Fetch all records from a table"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT * FROM {table_name}")
        return [dict(r) for r in rows]
