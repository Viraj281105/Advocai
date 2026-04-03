-- ============================================================
-- Migration: 003_add_embeddings.sql
-- Purpose: Enable pgvector + add embeddings to statutes
-- Safe to run multiple times
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. Ensure pgvector extension exists
-- ------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;

-- ------------------------------------------------------------
-- 2. Ensure statutes table exists (safety guard)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS statutes (
    id SERIAL PRIMARY KEY,
    statute_name TEXT,
    statute_text TEXT,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 3. Add embedding column if missing
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'statutes'
          AND column_name = 'embedding'
    ) THEN
        ALTER TABLE statutes
        ADD COLUMN embedding vector(768);
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 4. Create IVFFlat index (safe)
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS statutes_embedding_idx
ON statutes
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ------------------------------------------------------------
-- 5. Ensure migration tracking table exists
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- 6. Record migration (idempotent)
-- ------------------------------------------------------------
INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('003', 'add_embeddings', NOW())
ON CONFLICT (version) DO NOTHING;

COMMIT;