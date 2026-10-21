"""Tests des migrations Alembic : cohérence avec les modèles, contraintes et retour arrière."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from alembic import command
from app.core.config import get_settings
from app.db.base import Base

TEST_DB = "portail_migrations_test"


@pytest.fixture(scope="module")
def test_url():
    """Base PostgreSQL dédiée aux migrations ; retourne son URL."""
    url = make_url(get_settings().database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    yield url.set(database=TEST_DB).render_as_string(hide_password=False)
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture(scope="module")
def alembic_cfg(test_url):
    """Configuration Alembic pointant vers la base de test."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
    return cfg


def test_upgrade_matches_models(alembic_cfg, test_url):
    """Après migration, le schéma correspond aux modèles."""
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(test_url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []
    assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())


def test_constraints(alembic_cfg, test_url):
    """Les contraintes d'unicité et d'intégrité sont appliquées."""
    engine = create_engine(test_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash)"
                " VALUES (gen_random_uuid(), 'A@x.fr', 'h')"
            )
        )
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash)"
                " VALUES (gen_random_uuid(), 'b@x.fr', 'h')"
            )
        )
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash)"
                " VALUES (gen_random_uuid(), 'a@X.fr', 'h')"
            )
        )
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO invitations (id, inviter_id, invitee_id, status) "
                "SELECT gen_random_uuid(), id, id, 'pending' FROM users"
            )
        )


def test_downgrade(alembic_cfg, test_url):
    """Le retour à la version de base supprime les tables."""
    command.downgrade(alembic_cfg, "base")
    assert "users" not in inspect(create_engine(test_url)).get_table_names()
