# storage/session_manager.py — Hybrid Persistence Manager (Postgres + JSON Fallback)

from typing import Optional, Dict
import logging

from config.settings import PERSISTENCE_BACKEND, STAGE_ORDER
from storage.json.json_store import JSONStore  # always available

logger = logging.getLogger("SessionManager")

# Try to load Postgres backend
POSTGRES_AVAILABLE = False
BackendPG = None

if PERSISTENCE_BACKEND == "postgres":
    try:
        from storage.postgres.repository import Repository as BackendPG
        POSTGRES_AVAILABLE = True
    except Exception as e:
        logger.error(f"Postgres backend could not be loaded — falling back to JSON: {e}")
        POSTGRES_AVAILABLE = False


class SessionManager:
    """
    Hybrid Session Manager:
      - Prefers PostgreSQL
      - Falls back to JSON store if DB is unavailable
      - Ensures workflow ALWAYS makes forward progress
    """

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------
    @staticmethod
    def _use_postgres() -> bool:
        """Decides whether to use PostgreSQL or JSON."""
        return PERSISTENCE_BACKEND == "postgres" and POSTGRES_AVAILABLE

    # ----------------------------------------------------------------------
    # 1. Create Session
    # ----------------------------------------------------------------------
    @staticmethod
    def start_new_session(metadata: dict = None) -> str:
        if SessionManager._use_postgres():
            try:
                session_id = BackendPG.create_session(metadata)
                BackendPG.set_resume_flag(session_id, True, last_safe_stage=None)
                return session_id
            except Exception as e:
                logger.error(f"Postgres create_session() failed — switching to JSON: {e}")

        # JSON fallback
        import uuid
        session_id = str(uuid.uuid4())
        JSONStore.create_session(session_id, metadata or {})
        return session_id

    # ----------------------------------------------------------------------
    # 2. Resume Stage
    # ----------------------------------------------------------------------
    @staticmethod
    def get_resume_stage(session_id: str) -> Optional[str]:
        if SessionManager._use_postgres():
            try:
                state = BackendPG.get_resume_state(session_id)
                if state and state["is_resumable"]:
                    return state["last_safe_stage"]
            except Exception as e:
                logger.error(f"Postgres get_resume_stage() failed — fallback: {e}")

        # JSON path
        return JSONStore.get_last_completed_stage(session_id)

    # ----------------------------------------------------------------------
    # 3. Load Checkpoint
    # ----------------------------------------------------------------------
    @staticmethod
    def load_checkpoint(session_id: str, stage: str) -> Optional[Dict]:
        if SessionManager._use_postgres():
            try:
                return BackendPG.get_agent_output(session_id, stage)
            except Exception as e:
                logger.error(f"Postgres load_checkpoint() failed — fallback: {e}")

        return JSONStore.load_checkpoint(session_id, stage)

    # ----------------------------------------------------------------------
    # 4. Save Checkpoint
    # ----------------------------------------------------------------------
    @staticmethod
    def save_checkpoint(session_id: str, stage: str, output_json: dict, raw_text: str = None):
        """
        - Save to PostgreSQL if available.
        - If it fails → safe fallback to JSON store.
        """

        if SessionManager._use_postgres():
            try:
                BackendPG.save_agent_output(session_id, stage, output_json, raw_text)
                BackendPG.update_session_stage(session_id, stage)
                BackendPG.set_resume_flag(session_id, True, last_safe_stage=stage)
                return
            except Exception as e:
                logger.error(f"Postgres save_checkpoint() failed — falling back to JSON: {e}")

        # JSON fallback
        JSONStore.save_checkpoint(session_id, stage, output_json, raw_text)

    # ----------------------------------------------------------------------
    # 5. Log Failure
    # ----------------------------------------------------------------------
    @staticmethod
    def mark_failure(session_id: str, stage: str, error_message: str, error_type: str = None, traceback: str = None):
        if SessionManager._use_postgres():
            try:
                BackendPG.log_error(session_id, stage, error_message, error_type, traceback)
                BackendPG.set_resume_flag(session_id, False, last_safe_stage=stage)
                return
            except Exception as e:
                logger.error(f"Postgres mark_failure() failed — fallback to JSON: {e}")

        JSONStore.log_error(session_id, stage, error_message, error_type, traceback)

    # ----------------------------------------------------------------------
    # 6. Check if stage is completed
    # ----------------------------------------------------------------------
    @staticmethod
    def is_stage_completed(session_id: str, stage: str) -> bool:
        if SessionManager._use_postgres():
            try:
                last_stage = BackendPG.get_last_completed_stage(session_id)
                if not last_stage:
                    return False
                return STAGE_ORDER.index(last_stage) >= STAGE_ORDER.index(stage)
            except Exception as e:
                logger.error(f"Postgres is_stage_completed() failed — fallback: {e}")

        return JSONStore.stage_completed(session_id, stage)

    # ----------------------------------------------------------------------
    # 7. Should Skip a Stage?
    # ----------------------------------------------------------------------
    @staticmethod
    def should_skip_stage(session_id: str, stage: str) -> bool:
        if SessionManager._use_postgres():
            try:
                existing = BackendPG.get_agent_output(session_id, stage)
                return existing is not None
            except Exception as e:
                logger.error(f"Postgres should_skip_stage() failed — fallback: {e}")

        return JSONStore.stage_completed(session_id, stage)
