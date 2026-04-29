import asyncpg
import os
from dotenv import load_dotenv
import json
from urllib.parse import quote
from datetime import datetime, timezone

# import datetime

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
incident_date = datetime.now(timezone.utc)  # ✅ ingestion time
DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Use a pool for production
_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DSN, min_size=1, max_size=10)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
        CREATE TABLE IF NOT EXISTS public.master_decision_table (
            id SERIAL PRIMARY KEY,
            event_id TEXT NOT NULL,
            event_json JSONB NOT NULL,
            agents JSONB,
            selected_agents JSONB NOT NULL,
            reason TEXT,
            severity VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT now(),
            processed_at TIMESTAMPTZ,
            incident_date TIMESTAMPTZ DEFAULT now()
        );
    """
        )


async def insert_master_decision(
    event_id: str, event_json: dict, selected_agents: list, reason: str
):
    pool = await get_pool()
    severity = event_json.get("severity", None)  # Extract severity from JSON
    if isinstance(severity, list):
        severity = (
            severity[0] if severity else None
        )  # or ", ".join(severity) if you want all
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO master_decision_table (event_id, event_json, selected_agents, reason, severity, incident_date)
            VALUES ($1, $2::jsonb, $3::jsonb, $4, $5, $6)
            RETURNING id, created_at, incident_date;
            """,
            event_id,
            json.dumps(event_json),
            json.dumps(selected_agents),
            reason,
            severity,
            incident_date,
        )
        return dict(row)


async def fetch_pending_decisions(limit: int = 50):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, event_id, event_json, selected_agents, reason
            FROM master_decision_table
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT $1
            """,
            limit,
        )
        return [dict(r) for r in rows]


async def mark_decision_processing(decision_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE master_decision_table SET status='processing' WHERE id=$1",
            decision_id,
        )


async def mark_decision_processed(decision_id: int, success: bool = True):
    pool = await get_pool()
    async with pool.acquire() as conn:
        status = "processed" if success else "failed"
        await conn.execute(
            "UPDATE master_decision_table SET status=$1, processed_at = now() WHERE id=$2",
            status,
            decision_id,
        )
