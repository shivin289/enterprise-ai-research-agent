-- Enable pgvector extension. Run once against a fresh database.
-- In development, app/main.py's create_all() creates the tables; this
-- file documents the extension requirement and doubles as a reference
-- for the Alembic env you'd wire up for production migrations.
CREATE EXTENSION IF NOT EXISTS vector;
