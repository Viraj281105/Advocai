"""
orchestrator/auth/config.py
Load auth settings from environment with safe defaults for local dev.
In production set JWT_SECRET to a long random string via .env / secrets manager.
"""

import os
import secrets

# IMPORTANT: override this in production via environment variable
JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h
