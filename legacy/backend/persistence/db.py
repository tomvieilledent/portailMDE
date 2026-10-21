"""Database engine and session configuration for SQLAlchemy.

This module centralizes the engine creation, the session factory
(`SessionLocal`) and the declarative `Base` used by ORM models.

The database **schema is owned entirely by Alembic** (see ``alembic/versions``).
This module intentionally performs *no* schema work at import time: run
``alembic upgrade head`` to create or migrate the schema. Tests build their
schema from the ORM metadata directly (see ``tests/conftest.py``).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# default DB file placed in project root to avoid cwd-related permission issues
project_root = Path(__file__).resolve().parents[2]
default_db = project_root / 'data.db'
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db}")

# echo=True for debugging if needed
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Ensure the parent directory exists for a file-based SQLite DB so that both the
# app and Alembic can create the file on first connect. This is filesystem
# bookkeeping only — it never touches the schema.
if engine.url.drivername == 'sqlite' and engine.url.database:
    Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)
