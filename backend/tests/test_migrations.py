import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from app.core.config import get_settings
from app.db.base import Base

TEST_DB = "portail_test"


@pytest.fixture(scope="module")
def test_url():
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
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
    return cfg


def test_upgrade_matches_models(alembic_cfg, test_url):
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(test_url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []
    assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())


def test_constraints(alembic_cfg, test_url):
    engine = create_engine(test_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash)"
                " VALUES (gen_random_uuid(), 'A@x.fr', 'h')"
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
    command.downgrade(alembic_cfg, "base")
    assert "users" not in inspect(create_engine(test_url)).get_table_names()
