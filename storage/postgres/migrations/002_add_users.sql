-- storage/postgres/migrations/002_add_users.sql
-- Issue #9 — Backend: Add JWT authentication and user-scoped sessions
-- Run: psql $POSTGRES_URL -f storage/postgres/migrations/002_add_users.sql

BEGIN;

-- -------------------------------------------------------------------------
-- 1. Users table
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    email            TEXT UNIQUE NOT NULL,
    hashed_password  TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- -------------------------------------------------------------------------
-- 2. Add user_id FK to cases table
--    Assumes an existing `cases` table created in 001_initial.sql
-- -------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'cases'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'cases' AND column_name = 'user_id'
        ) THEN
            ALTER TABLE cases ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
            CREATE INDEX idx_cases_user_id ON cases (user_id);
        END IF;
    END IF;
END;
$$;

-- -------------------------------------------------------------------------
-- 3. Trigger: keep updated_at fresh on users
-- -------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
