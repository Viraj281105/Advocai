"""
orchestrator/auth/db.py
PostgreSQL helpers for the users table.
Uses the same psycopg2 connection pattern already in the project.
"""

import uuid
from dataclasses import dataclass
from typing import Optional

import psycopg2
import psycopg2.extras

from ..storage.postgres import get_connection  # reuse existing pool / conn helper


# ─── Schema (run once — idempotent) ───────────────────────────────────────────

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT        NOT NULL,
    email         TEXT        NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS users_email_idx ON users (email);
"""


def ensure_users_table() -> None:
    """Call once at startup to create the table if it doesn't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_USERS_TABLE)
        conn.commit()


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class UserRecord:
    id: uuid.UUID
    name: str
    email: str
    password_hash: str


# ─── Queries ──────────────────────────────────────────────────────────────────

async def get_user_by_email(email: str) -> Optional[UserRecord]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (email,))
            row = cur.fetchone()
    if row is None:
        return None
    return UserRecord(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
    )


async def create_user(name: str, email: str, password_hash: str) -> UserRecord:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (name, email, password_hash),
            )
            row = cur.fetchone()
        conn.commit()
    return UserRecord(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
    )
