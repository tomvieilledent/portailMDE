import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models import Company, User
from app.models.enums import UserRole

TEST_DB = "portail_test"


@pytest.fixture(scope="session")
def engine():
    """Base PostgreSQL dédiée aux tests, migrée jusqu'à ``head``."""
    url = make_url(get_settings().database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    test_url = url.set(database=TEST_DB).render_as_string(hide_password=False)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
    command.upgrade(cfg, "head")
    eng = create_engine(test_url)
    yield eng
    eng.dispose()
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture
def session(engine):
    """Session de test ; toutes les tables sont vidées à la fin de chaque test."""
    with sessionmaker(bind=engine, expire_on_commit=False)() as s:
        yield s
    with engine.begin() as conn:
        tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        conn.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture
def client(session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def make_user(session: Session):
    """Fabrique d'utilisateurs ; mot de passe par défaut : ``password123``."""

    def _make(email="user@example.fr", password="password123", **kwargs) -> User:
        user = User(email=email, password_hash=hash_password(password), **kwargs)
        session.add(user)
        session.commit()
        return user

    return _make


@pytest.fixture
def make_company(session: Session):
    def _make(name="Acme", **kwargs) -> Company:
        company = Company(name=name, **kwargs)
        session.add(company)
        session.commit()
        return company

    return _make


@pytest.fixture
def login(client: TestClient):
    """Connecte un utilisateur et retourne les en-têtes d'autorisation."""

    def _login(email="user@example.fr", password="password123") -> dict[str, str]:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


__all__ = ["UserRole"]


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Les fichiers envoyés pendant un test vont dans un dossier temporaire."""
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _no_scheduler(monkeypatch):
    """Pas de tâches planifiées pendant les tests."""
    monkeypatch.setenv("NEWS_SYNC_ENABLED", "false")
