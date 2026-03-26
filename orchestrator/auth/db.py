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
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "advocai"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


# ─── Schema ───────────────────────────────────────────────────────────────────

CREATE_USERS_TABLE = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
    id: uuid.UUID
    name: str
    email: str
    password_hash: str


# ─── Queries (SYNC — FIXED) ───────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[UserRecord]:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, email, password_hash FROM users WHERE email = %s LIMIT 1",
                (email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return UserRecord(**row)


def create_user(name: str, email: str, password_hash: str) -> UserRecord:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, name, email, password_hash
                """,
                (name, email, password_hash),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    return UserRecord(**row)