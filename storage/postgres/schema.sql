-- ============================================================
--  AdvocAI Phase II — PostgreSQL Schema
--  Durable Sessions | Agent Checkpoints | Workflow Resilience
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. sessions — Tracks one full workflow run
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- last successfully completed stage
    last_completed_stage TEXT,

    -- optional metadata
    metadata          JSONB DEFAULT '{}'::JSONB
);

-- Index for fast querying by latest updated
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
    ON sessions (updated_at DESC);


-- ============================================================
-- 2. agent_outputs — Stores each agent's output in JSONB
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_outputs (
    id               BIGSERIAL PRIMARY KEY,
    session_id       UUID REFERENCES sessions(session_id) ON DELETE CASCADE,

    agent_stage      TEXT NOT NULL,   -- auditor / clinician / regulatory / barrister / judge
    output_json      JSONB NOT NULL,  -- raw structured output
    raw_text         TEXT,            -- optional raw LLM text

    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One stage per session is usually expected — enforce uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_outputs_unique_stage
    ON agent_outputs (session_id, agent_stage);

-- JSON indexing for search/debug/analysis
CREATE INDEX IF NOT EXISTS idx_agent_outputs_gin
    ON agent_outputs USING GIN (output_json);


-- ============================================================
-- 3. workflow_errors — Records failures for debugging & recovery
-- ============================================================
CREATE TABLE IF NOT EXISTS workflow_errors (
    id               BIGSERIAL PRIMARY KEY,
    session_id       UUID REFERENCES sessions(session_id) ON DELETE CASCADE,

    agent_stage      TEXT,            -- which agent failed
    error_message    TEXT NOT NULL,   -- Python/LLM/error details
    error_type       TEXT,            -- Timeout, ValidationError, LLMError, etc.
    traceback        TEXT,            -- optional Python stacktrace

    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_errors_session
    ON workflow_errors (session_id);


-- ============================================================
-- 4. resume_flags — Lightweight, makes resume/pause trivial
-- ============================================================
CREATE TABLE IF NOT EXISTS resume_flags (
    session_id       UUID PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,

    is_resumable     BOOLEAN NOT NULL DEFAULT TRUE,
    last_safe_stage  TEXT,

    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 5. Triggers — auto-update updated_at on sessions
-- ============================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_sessions ON sessions;

CREATE TRIGGER trg_update_sessions
BEFORE UPDATE ON sessions
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================
-- End of Schema
-- ============================================================
