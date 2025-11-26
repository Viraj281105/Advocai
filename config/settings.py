# config/settings.py — Global configuration for AdvocAI Phase II

import os
from dotenv import load_dotenv

# Load .env at module import
load_dotenv()

# ------------------------------------------------------------------------------
# ENVIRONMENT & BACKEND CONFIG
# ------------------------------------------------------------------------------

# Which persistence backend to use?
# "postgres"  = production (full resilience)
# "json"      = lightweight local dev mode
PERSISTENCE_BACKEND = os.getenv("PERSISTENCE_BACKEND", "postgres").lower()


# ------------------------------------------------------------------------------
# DATABASE CONFIG (PostgreSQL)
# ------------------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "advocai")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Should connection pooling be enabled?
DB_ENABLE_POOL = os.getenv("DB_ENABLE_POOL", "true").lower() == "true"


# ------------------------------------------------------------------------------
# GEMINI / GENAI CONFIG
# ------------------------------------------------------------------------------
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-pro")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ------------------------------------------------------------------------------
# SESSION & STORAGE PATHS
# ------------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")        # used by JSON backend
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")


# ------------------------------------------------------------------------------
# FEATURE FLAGS (phased upgrades)
# ------------------------------------------------------------------------------
ENABLE_RESUME = True              # Enables pause/resume workflows
ENABLE_CHECKPOINTING = True       # Enables saving after each stage
ENABLE_ERROR_LOGGING = True       # Enables detailed error tracking
ENABLE_JSON_BACKUP = True         # Always save a local copy of checkpoints


# ------------------------------------------------------------------------------
# ORDER OF STAGES (single source of truth)
# ------------------------------------------------------------------------------
STAGE_ORDER = [
    "auditor",
    "clinician",
    "regulatory",
    "barrister",
    "judge"
]


# ------------------------------------------------------------------------------
# Create directories if missing (safe for both dev + production)
# ------------------------------------------------------------------------------

for path in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, SESSIONS_DIR]:
    os.makedirs(path, exist_ok=True)
