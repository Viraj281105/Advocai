-- Migration: 003_add_embeddings.sql
-- Adds pgvector extension and embedding column to statutes table
-- Run this after 001 and 002 migrations

-- Enable pgvector extension (requires PostgreSQL with pgvector installed)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to statutes table (768 dimensions for Gemini text-embedding-004)
ALTER TABLE statutes
    ADD COLUMN IF NOT EXISTS embedding vector(768);

-- Create an IVFFlat index for fast approximate nearest-neighbor search
-- lists = 100 is a good default for tables with up to ~1M rows
CREATE INDEX IF NOT EXISTS statutes_embedding_idx
    ON statutes
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Track migration
INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('003', 'add_embeddings', NOW())
ON CONFLICT (version) DO NOTHING;
