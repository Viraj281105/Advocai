# storage/postgres/repository.py

import json
from psycopg2.extras import Json
from storage.postgres.connection import PostgresConnection


class Repository:
    """
    PostgreSQL Repository Layer — handles all read/write DB operations.
    This is the backbone of AdvocAI’s resilient workflow management.
    """

    # ============================================================
    # 1. Create a new workflow session
    # ============================================================
    @staticmethod
    def create_session(metadata: dict = None) -> str:
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO sessions (metadata)
                VALUES (%s)
                RETURNING session_id;
                """,
                (Json(metadata) if metadata else Json({}),)
            )
            session_id = cur.fetchone()[0]
            conn.commit()
            return str(session_id)
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 2. Update session stage checkpoint
    # ============================================================
    @staticmethod
    def update_session_stage(session_id: str, stage: str):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE sessions
                SET last_completed_stage = %s
                WHERE session_id = %s;
                """,
                (stage, session_id)
            )
            conn.commit()
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 3. Save agent output (JSONB)
    # ============================================================
    @staticmethod
    def save_agent_output(session_id: str, stage: str, output_json: dict, raw_text: str = None):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO agent_outputs (session_id, agent_stage, output_json, raw_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id, agent_stage)
                DO UPDATE SET
                    output_json = EXCLUDED.output_json,
                    raw_text = EXCLUDED.raw_text,
                    created_at = NOW();
                """,
                (session_id, stage, Json(output_json), raw_text)
            )
            conn.commit()
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 4. Retrieve agent output
    # ============================================================
    @staticmethod
    def get_agent_output(session_id: str, stage: str):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT output_json, raw_text
                FROM agent_outputs
                WHERE session_id = %s AND agent_stage = %s;
                """,
                (session_id, stage)
            )
            row = cur.fetchone()
            if row:
                return {
                    "output_json": row[0],
                    "raw_text": row[1]
                }
            return None
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 5. Log workflow errors
    # ============================================================
    @staticmethod
    def log_error(session_id: str, stage: str, error_message: str, error_type: str = None, traceback: str = None):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO workflow_errors (session_id, agent_stage, error_message, error_type, traceback)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (session_id, stage, error_message, error_type, traceback)
            )
            conn.commit()
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 6. Resume flags — write
    # ============================================================
    @staticmethod
    def set_resume_flag(session_id: str, is_resumable: bool, last_safe_stage: str):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO resume_flags (session_id, is_resumable, last_safe_stage)
                VALUES (%s, %s, %s)
                ON CONFLICT (session_id)
                DO UPDATE SET
                    is_resumable = EXCLUDED.is_resumable,
                    last_safe_stage = EXCLUDED.last_safe_stage,
                    updated_at = NOW();
                """,
                (session_id, is_resumable, last_safe_stage)
            )
            conn.commit()
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 7. Resume flags — read
    # ============================================================
    @staticmethod
    def get_resume_state(session_id: str):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT is_resumable, last_safe_stage
                FROM resume_flags
                WHERE session_id = %s;
                """,
                (session_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "is_resumable": row[0],
                    "last_safe_stage": row[1]
                }
            return None
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)

    # ============================================================
    # 8. Get last completed stage
    # ============================================================
    @staticmethod
    def get_last_completed_stage(session_id: str):
        conn = PostgresConnection.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT last_completed_stage
                FROM sessions
                WHERE session_id = %s;
                """,
                (session_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            cur.close()
            PostgresConnection.return_connection(conn)
