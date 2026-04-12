"""
orchestrator/auth/db.py
PostgreSQL helpers for the users table.
"""

import os
import uuid
from dataclasses import dataclass
from typing import Optional

import psycopg2
import psycopg2.extras


# ─── Connection ───────────────────────────────────────────────────────────────

def _get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "advocai"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )
# ─── Schema ───────────────────────────────────────────────────────────────────

# Matches the actual DB schema — no name column, uses hashed_password
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS users_email_idx ON users (email);
"""


def ensure_users_table() -> None:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_USERS_TABLE)
        conn.commit()
    finally:
        conn.close()


# ─── Model ────────────────────────────────────────────────────────────────────

@dataclass
class UserRecord:
    id: int
    email: str
    hashed_password: str
    created_at: object = None
    updated_at: object = None


# ─── Queries ──────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[UserRecord]:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, email, hashed_password, created_at, updated_at
                FROM users WHERE email = %s LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return UserRecord(**row)


def create_user(email: str, hashed_password: str) -> UserRecord:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (email, hashed_password)
                VALUES (%s, %s)
                RETURNING id, email, hashed_password, created_at, updated_at
                """,
                (email, hashed_password),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return UserRecord(**row)